from django.conf.urls.defaults import patterns, url
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, MultipleObjectsReturned
from django.core.urlresolvers import NoReverseMatch, reverse, resolve, Resolver404
from django.db.models.sql.constants import QUERY_TERMS, LOOKUP_SEP
from django.http import HttpResponse
from tastypie.authentication import Authentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.bundle import Bundle
from tastypie.cache import NoCache
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.exceptions import NotFound, BadRequest, InvalidFilterError, HydrationError, InvalidSortError, ImmediateHttpResponse
from tastypie.fields import *
from tastypie.http import *
from tastypie.paginator import Paginator
from tastypie.serializers import Serializer
from tastypie.throttle import BaseThrottle
from tastypie.utils import is_valid_jsonp_callback_value, dict_strip_unicode_keys
from tastypie.utils.mime import determine_format, build_content_type
try:
    set
except NameError:
    from sets import Set as set
# The ``copy`` module was added in Python 2.5 and ``copycompat`` was added in
# post 1.1.1 Django (r11901)
try:
    from django.utils.copycompat import deepcopy
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    from copy import deepcopy
    def csrf_exempt(func):
        return func


class ResourceOptions(object):
    """
    A configuration class for ``Resource``.
    
    Provides sane defaults and the logic needed to augment these settings with
    the internal ``class Meta`` used on ``Resource`` subclasses.
    """
    serializer = Serializer()
    authentication = Authentication()
    authorization = ReadOnlyAuthorization()
    cache = NoCache()
    throttle = BaseThrottle()
    allowed_methods = None
    list_allowed_methods = ['get', 'post', 'put', 'delete']
    detail_allowed_methods = ['get', 'post', 'put', 'delete']
    limit = 20
    api_name = None
    resource_name = None
    default_format = 'application/json'
    filtering = {}
    ordering = []
    object_class = None
    queryset = None
    fields = []
    excludes = []
    include_resource_uri = True
    include_absolute_url = False
    
    def __new__(cls, meta=None):
        overrides = {}

        # Handle overrides.
        if meta:
            for override_name, override_value in meta.__dict__.items():
                # No internals please.
                if not override_name.startswith('_'):
                    overrides[override_name] = override_value
        
        # Shortcut to specify both at the class level.
        if overrides.get('allowed_methods', None) is not None:
            overrides['list_allowed_methods'] = overrides['allowed_methods']
            overrides['detail_allowed_methods'] = overrides['allowed_methods']
        
        if not overrides.get('queryset', None) is None:
            overrides['object_class'] = overrides['queryset'].model
        
        return object.__new__(type('ResourceOptions', (cls,), overrides))


class DeclarativeMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = {}
        declared_fields = {}
        
        # Inherit any fields from parent(s).
        try:
            parents = [b for b in bases if issubclass(b, Resource)]
            
            for p in parents:
                fields = getattr(p, 'base_fields', None)
                
                if fields:
                    attrs['base_fields'].update(fields)
        except NameError:
            pass
        
        for field_name, obj in attrs.items():
            if isinstance(obj, ApiField):
                field = attrs.pop(field_name)
                field.instance_name = field_name
                declared_fields[field_name] = field
        
        attrs['base_fields'].update(declared_fields)
        attrs['declared_fields'] = declared_fields
        new_class = super(DeclarativeMetaclass, cls).__new__(cls, name, bases, attrs)
        opts = getattr(new_class, 'Meta', None)
        new_class._meta = ResourceOptions(opts)
        
        if not getattr(new_class._meta, 'resource_name', None):
            # No ``resource_name`` provided. Attempt to auto-name the resource.
            class_name = new_class.__name__
            name_bits = [bit for bit in class_name.split('Resource') if bit]
            resource_name = ''.join(name_bits).lower()
            new_class._meta.resource_name = resource_name
        
        if getattr(new_class._meta, 'include_resource_uri', True):
            if not 'resource_uri' in new_class.base_fields:
                new_class.base_fields['resource_uri'] = CharField(readonly=True)
        elif 'resource_uri' in new_class.base_fields and not 'resource_uri' in attrs:
            del(new_class.base_fields['resource_uri'])
        
        for field_name, field_object in new_class.base_fields.items():
            # Cover self-referential Resources.
            # We can't do this quite like Django because there's no ``AppCache``
            # here (which I think we should avoid as long as possible).
            if isinstance(field_object, RelatedField):
                if field_object.self_referential or field_object.to == 'self':
                    field_object.to = new_class
        
        return new_class


class Resource(object):
    """
    Handles the data, request dispatch and responding to requests.
    
    Serialization/deserialization is handled "at the edges" (i.e. at the
    beginning/end of the request/response cycle) so that everything internally
    is Python data structures.
    
    This class tries to be non-model specific, so it can be hooked up to other
    data sources, such as search results, files, other data, etc.
    """
    __metaclass__ = DeclarativeMetaclass
    
    def __init__(self, api_name=None):
        self.fields = deepcopy(self.base_fields)
        
        if not api_name is None:
            self._meta.api_name = api_name
    
    def __getattr__(self, name):
        if name in self.fields:
            return self.fields[name]
    
    def wrap_view(self, view):
        """
        Wraps methods so they can be called in a more functional way as well
        as handling exceptions better.
        
        Note that if ``BadRequest`` or an exception with a ``response`` attr
        are seen, there is special handling to either present a message back
        to the user or return the response traveling with the exception.
        """
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            try:
                return getattr(self, view)(request, *args, **kwargs)
            except BadRequest, e:
                return HttpBadRequest(e.args[0])
            except Exception, e:
                if hasattr(e, 'response'):
                    return e.response
                
                # A real, non-expected exception. Re-raise it.
                raise
        
        return wrapper
    
    @property
    def urls(self):
        """
        The endpoints this ``Resource`` responds to.
        
        Mostly a standard URLconf, this is suitable for either automatic use
        when registered with an ``Api`` class or for including directly in
        a URLconf should you choose to.
        """
        urlpatterns = patterns('',
            url(r"^(?P<resource_name>%s)/$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema/$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<pk_list>\w[\w/;-]*)/$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        )
        return urlpatterns
    
    def determine_format(self, request):
        """
        Used to determine the desired format.
        
        Largely relies on ``tastypie.utils.mime.determine_format`` but here
        as a point of extension.
        """
        return determine_format(request, self._meta.serializer, default_format=self._meta.default_format)
    
    def serialize(self, request, data, format, options=None):
        """
        Given a request, data and a desired format, produces a serialized
        version suitable for transfer over the wire.
        
        Mostly a hook, this uses the ``Serializer`` from ``Resource._meta``.
        """
        options = options or {}
        
        if 'text/javascript' in format:
            # get JSONP callback name. default to "callback"
            callback = request.GET.get('callback', 'callback')
            
            if not is_valid_jsonp_callback_value(callback):
                raise BadRequest('JSONP callback name is invalid.')
            
            options['callback'] = callback
        
        return self._meta.serializer.serialize(data, format, options)
    
    def deserialize(self, request, data, format='application/json'):
        """
        Given a request, data and a format, deserializes the given data.
        
        It relies on the request properly sending a ``CONTENT_TYPE`` header,
        falling back to ``application/json`` if not provided.
        
        Mostly a hook, this uses the ``Serializer`` from ``Resource._meta``.
        """
        return self._meta.serializer.deserialize(data, format=request.META.get('CONTENT_TYPE', 'application/json'))
    
    def dispatch_list(self, request, **kwargs):
        """
        A view for handling the various HTTP methods (GET/POST/PUT/DELETE) over
        the entire list of resources.
        
        Relies on ``Resource.dispatch`` for the heavy-lifting.
        """
        return self.dispatch('list', request, **kwargs)
    
    def dispatch_detail(self, request, **kwargs):
        """
        A view for handling the various HTTP methods (GET/POST/PUT/DELETE) on
        a single resource.
        
        Relies on ``Resource.dispatch`` for the heavy-lifting.
        """
        return self.dispatch('detail', request, **kwargs)
    
    def dispatch(self, request_type, request, **kwargs):
        """
        Handles the common operations (allowed HTTP method, authentication,
        throttling, method lookup) surrounding most CRUD interactions.
        """
        allowed_methods = getattr(self._meta, "%s_allowed_methods" % request_type, None)
        request_method = self.method_check(request, allowed=allowed_methods)
        
        method = getattr(self, "%s_%s" % (request_method, request_type), None)
        
        if method is None:
            raise ImmediateHttpResponse(response=HttpNotImplemented())
        
        self.is_authenticated(request)
        self.is_authorized(request)
        self.throttle_check(request)
        
        # All clear. Process the request.
        request = convert_post_to_put(request)
        response = method(request, **kwargs)
        
        # Add the throttled request.
        self.log_throttled_access(request)
        
        # If what comes back isn't a ``HttpResponse``, assume that the
        # request was accepted and that some action occurred. This also
        # prevents Django from freaking out.
        if not isinstance(response, HttpResponse):
            return HttpAccepted()
        
        return response
    
    def remove_api_resource_names(self, url_dict):
        """
        Given a dictionary of regex matches from a URLconf, removes
        ``api_name`` and/or ``resource_name`` if found.
        
        This is useful for converting URLconf matches into something suitable
        for data lookup. For example::
        
            Model.objects.filter(**self.remove_api_resource_names(matches))
        """
        kwargs_subset = url_dict.copy()
        
        for key in ['api_name', 'resource_name']:
            try:
                del(kwargs_subset[key])
            except KeyError:
                pass
        
        return kwargs_subset
    
    def method_check(self, request, allowed=None):
        """
        Ensures that the HTTP method used on the request is allowed to be
        handled by the resource.
        
        Takes an ``allowed`` parameter, which should be a list of lowercase
        HTTP methods to check against. Usually, this looks like::
        
            # The most generic lookup.
            self.method_check(request, self._meta.allowed_methods)
            
            # A lookup against what's allowed for list-type methods.
            self.method_check(request, self._meta.list_allowed_methods)
            
            # A useful check when creating a new endpoint that only handles
            # GET.
            self.method_check(request, ['get'])
        """
        if allowed is None:
            allowed = []
        
        request_method = request.method.lower()
        
        if not request_method in allowed:
            raise ImmediateHttpResponse(response=HttpMethodNotAllowed())
        
        return request_method

    def is_authorized(self, request, object=None):
        """
        Handles checking of permissions to see if the user has authorization
        to GET, POST, PUT, or DELETE this resource.  If ``object`` is provided,
        the authorization backend can apply additional row-level permissions
        checking.
        """
        auth_result = self._meta.authorization.is_authorized(request, object)

        if isinstance(auth_result, HttpResponse):
            raise ImmediateHttpResponse(response=auth_result)
        
        if not auth_result is True:
            raise ImmediateHttpResponse(response=HttpUnauthorized())
    
    def is_authenticated(self, request):
        """
        Handles checking if the user is authenticated and dealing with
        unauthenticated users.
        
        Mostly a hook, this uses class assigned to ``authentication`` from
        ``Resource._meta``.
        """
        # Authenticate the request as needed.
        auth_result = self._meta.authentication.is_authenticated(request)
        
        if isinstance(auth_result, HttpResponse):
            raise ImmediateHttpResponse(response=auth_result)
        
        if not auth_result is True:
            raise ImmediateHttpResponse(response=HttpUnauthorized())
    
    def throttle_check(self, request):
        """
        Handles checking if the user should be throttled.
        
        Mostly a hook, this uses class assigned to ``throttle`` from
        ``Resource._meta``.
        """
        identifier = self._meta.authentication.get_identifier(request)
        
        # Check to see if they should be throttled.
        if self._meta.throttle.should_be_throttled(identifier):
            # Throttle limit exceeded.
            raise ImmediateHttpResponse(response=HttpForbidden())
    
    def log_throttled_access(self, request):
        """
        Handles the recording of the user's access for throttling purposes.
        
        Mostly a hook, this uses class assigned to ``throttle`` from
        ``Resource._meta``.
        """
        request_method = request.method.lower()
        self._meta.throttle.accessed(self._meta.authentication.get_identifier(request), url=request.get_full_path(), request_method=request_method)
    
    def build_bundle(self, obj=None, data=None):
        """
        Given either an object, a data dictionary or both, builds a ``Bundle``
        for use throughout the ``dehydrate/hydrate`` cycle.
        
        If no object is provided, an empty object from
        ``Resource._meta.object_class`` is created so that attempts to access
        ``bundle.obj`` do not fail.
        """
        if obj is None:
            obj = self._meta.object_class()
        
        return Bundle(obj, data)
    
    def build_filters(self, filters=None):
        """
        Allows for the filtering of applicable objects.
        
        This needs to be implemented at the user level.'
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        return filters
    
    def apply_sorting(self, obj_list, options=None):
        """
        Allows for the sorting of objects being returned.
        
        This needs to be implemented at the user level.
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        return obj_list
    
    # URL-related methods.
    
    def get_resource_uri(self, bundle_or_obj):
        """
        This needs to be implemented at the user level.
        
        A ``return reverse("api_dispatch_detail", kwargs={'resource_name':
        self.resource_name, 'pk': object.id})`` should be all that would
        be needed.
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        raise NotImplementedError()
    
    def get_resource_list_uri(self):
        """
        Returns a URL specific to this resource's list endpoint.
        """
        kwargs = {
            'resource_name': self._meta.resource_name,
        }
        
        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name
        
        try:
            return reverse("api_dispatch_list", kwargs=kwargs)
        except NoReverseMatch:
            return None
    
    def get_via_uri(self, uri):
        """
        This pulls apart the salient bits of the URI and populates the
        resource via a ``obj_get``.
        
        If you need custom behavior based on other portions of the URI,
        simply override this method.
        """
        try:
            view, args, kwargs = resolve(uri)
        except Resolver404:
            raise NotFound("The URL provided '%s' was not a link to a valid resource." % uri)
        
        return self.obj_get(**self.remove_api_resource_names(kwargs))
    
    # Data preparation.
    
    def full_dehydrate(self, obj):
        """
        Given an object instance, extract the information from it to populate
        the resource.
        """
        bundle = Bundle(obj=obj)
        
        # Dehydrate each field.
        for field_name, field_object in self.fields.items():
            # A touch leaky but it makes URI resolution work.
            if isinstance(field_object, RelatedField):
                field_object.api_name = self._meta.api_name
                field_object.resource_name = self._meta.resource_name
                
            bundle.data[field_name] = field_object.dehydrate(bundle)
        
        # Run through optional overrides.
        for field_name, field_object in self.fields.items():
            method = getattr(self, "dehydrate_%s" % field_name, None)
            
            if method:
                bundle.data[field_name] = method(bundle)
        
        bundle = self.dehydrate(bundle)
        return bundle
    
    def dehydrate(self, bundle):
        """
        A hook to allow a final manipulation of data once all fields/methods
        have built out the dehydrated data.
        
        Useful if you need to access more than one dehydrated field or want
        to annotate on additional data.
        
        Must return the modified bundle.
        """
        return bundle
    
    def full_hydrate(self, bundle):
        """
        Given a populated bundle, distill it and turn it back into
        a full-fledged object instance.
        """
        if bundle.obj is None:
            bundle.obj = self._meta.object_class()
        
        for field_name, field_object in self.fields.items():
            if field_object.attribute:
                value = field_object.hydrate(bundle)
                
                if value is not None:
                    # We need to avoid populating M2M data here as that will
                    # cause things to blow up.
                    if not getattr(field_object, 'is_related', False):
                        setattr(bundle.obj, field_object.attribute, value)
                    elif not getattr(field_object, 'is_m2m', False):
                        setattr(bundle.obj, field_object.attribute, value.obj)
        
        for field_name, field_object in self.fields.items():
            method = getattr(self, "hydrate_%s" % field_name, None)
            
            if method:
                bundle = method(bundle)
        
        bundle = self.hydrate(bundle)
        return bundle
    
    def hydrate(self, bundle):
        """
        A hook to allow a final manipulation of data once all fields/methods
        have built out the hydrated data.
        
        Useful if you need to access more than one hydrated field or want
        to annotate on additional data.
        
        Must return the modified bundle.
        """
        return bundle
    
    def hydrate_m2m(self, bundle):
        """
        Populate the ManyToMany data on the instance.
        """
        if bundle.obj is None:
            raise HydrationError("You must call 'full_hydrate' before attempting to run 'hydrate_m2m' on %r." % self)
        
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_m2m', False):
                continue
            
            if field_object.attribute:
                # Note that we only hydrate the data, leaving the instance
                # unmodified. It's up to the user's code to handle this.
                # The ``ModelResource`` provides a working baseline
                # in this regard.
                bundle.data[field_name] = field_object.hydrate_m2m(bundle)
        
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_m2m', False):
                continue
            
            method = getattr(self, "hydrate_%s" % field_name, None)
            
            if method:
                method(bundle)
        
        return bundle
    
    def build_schema(self):
        """
        Returns a dictionary of all the fields on the resource and some
        properties about those fields.
        
        Used by the ``schema/`` endpoint to describe what will be available.
        """
        data = {}
        
        for field_name, field_object in self.fields.items():
            data[field_name] = {
                'type': field_object.dehydrated_type,
                'nullable': field_object.null,
                'readonly': field_object.readonly,
                # FIXME: Include what filters are available.
                # FIXME: Include if sorting is available on the field.
            }
        
        return data
    
    def dehydrate_resource_uri(self, bundle):
        """
        For the automatically included ``resource_uri`` field, dehydrate
        the URI for the given bundle.
        
        Returns empty string if no URI can be generated.
        """
        try:
            return self.get_resource_uri(bundle)
        except NotImplementedError:
            return ''
        except NoReverseMatch:
            return ''
    
    def generate_cache_key(self, *args, **kwargs):
        """
        Creates a unique-enough cache key.
        
        This is based off the current api_name/resource_name/args/kwargs.
        """
        smooshed = []
        
        for key, value in kwargs.items():
            smooshed.append("%s=%s" % (key, value))
        
        # Use a list plus a ``.join()`` because it's faster than concatenation.
        return "%s:%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, ':'.join(args), ':'.join(smooshed))
    
    # Data access methods.
    
    def obj_get_list(self, filters=None, **kwargs):
        """
        Fetches the list of objects available on the resource.
        
        This needs to be implemented at the user level.
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        raise NotImplementedError()
    
    def cached_obj_get_list(self, **kwargs):
        """
        A version of ``obj_get_list`` that uses the cache as a means to get
        commonly-accessed data faster.
        """
        cache_key = self.generate_cache_key('list', **kwargs)
        obj_list = self._meta.cache.get(cache_key)
        
        if obj_list is None:
            obj_list = self.obj_get_list(**kwargs)
            self._meta.cache.set(cache_key, obj_list)
        
        return obj_list
    
    def obj_get(self, **kwargs):
        """
        Fetches an individual object on the resource.
        
        This needs to be implemented at the user level. If the object can not
        be found, this should raise a ``NotFound`` exception.
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        raise NotImplementedError()
    
    def cached_obj_get(self, **kwargs):
        """
        A version of ``obj_get`` that uses the cache as a means to get
        commonly-accessed data faster.
        """
        cache_key = self.generate_cache_key('detail', **kwargs)
        bundle = self._meta.cache.get(cache_key)
        
        if bundle is None:
            bundle = self.obj_get(**kwargs)
            self._meta.cache.set(cache_key, bundle)
        
        return bundle
    
    def obj_create(self, bundle, **kwargs):
        """
        Creates a new object based on the provided data.
        
        This needs to be implemented at the user level.
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        raise NotImplementedError()
    
    def obj_update(self, bundle, **kwargs):
        """
        Updates an existing object (or creates a new object) based on the
        provided data.
        
        This needs to be implemented at the user level.
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        raise NotImplementedError()
    
    def obj_delete_list(self, **kwargs):
        """
        Deletes an entire list of objects.
        
        This needs to be implemented at the user level.
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        raise NotImplementedError()
    
    def obj_delete(self):
        """
        Deletes a single object.
        
        This needs to be implemented at the user level.
        
        ``ModelResource`` includes a full working version specific to Django's
        ``Models``.
        """
        raise NotImplementedError()
    
    def create_response(self, request, data):
        """
        Extracts the common "which-format/serialize/return-response" cycle.
        
        Mostly a useful shortcut/hook.
        """
        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)
        return HttpResponse(content=serialized, content_type=build_content_type(desired_format))
    
    # Views.
    
    def get_list(self, request, **kwargs):
        """
        Returns a serialized list of resources.
        
        Calls ``obj_get_list`` to provide the data, then handles that result
        set and serializes it.
        
        Should return a HttpResponse (200 OK).
        """
        # TODO: Uncached for now. Invalidation that works for everyone may be
        #       impossible.
        objects = self.obj_get_list(filters=request.GET, **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET)
        
        paginator = Paginator(request.GET, sorted_objects, resource_uri=self.get_resource_list_uri())
        to_be_serialized = paginator.page()
        
        # Dehydrate the bundles in preparation for serialization.
        to_be_serialized['objects'] = [self.full_dehydrate(obj=obj) for obj in to_be_serialized['objects']]
        return self.create_response(request, to_be_serialized)
    
    def get_detail(self, request, **kwargs):
        """
        Returns a single serialized resource.
        
        Calls ``cached_obj_get/obj_get`` to provide the data, then handles that result
        set and serializes it.
        
        Should return a HttpResponse (200 OK).
        """
        try:
            obj = self.cached_obj_get(**self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")
        
        bundle = self.full_dehydrate(obj)
        return self.create_response(request, bundle)
    
    def put_list(self, request, **kwargs):
        """
        Replaces a collection of resources with another collection.
        
        Calls ``delete_list`` to clear out the collection then ``obj_create``
        with the provided the data to create the new collection.
        
        Return ``HttpAccepted`` (204 No Content).
        """
        deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        
        if not 'objects' in deserialized:
            raise BadRequest("Invalid data sent.")
        
        self.obj_delete_list(**self.remove_api_resource_names(kwargs))
        
        for object_data in deserialized['objects']:
            data = {}
            
            for key, value in object_data.items():
                data[str(key)] = value
            
            bundle = self.build_bundle(data=data)
            self.obj_create(bundle)
        
        return HttpAccepted()
    
    def put_detail(self, request, **kwargs):
        """
        Either updates an existing resource or creates a new one with the
        provided data.
        
        Calls ``obj_update`` with the provided data first, but falls back to
        ``obj_create`` if the object does not already exist.
        
        If a new resource is created, return ``HttpCreated`` (201 Created).
        If an existing resource is modified, return ``HttpAccepted`` (204 No Content).
        """
        deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))
        
        try:
            updated_bundle = self.obj_update(bundle, pk=kwargs.get('pk'))
            return HttpAccepted()
        except:
            updated_bundle = self.obj_create(bundle, pk=kwargs.get('pk'))
            return HttpCreated(location=self.get_resource_uri(updated_bundle))
    
    def post_list(self, request, **kwargs):
        """
        Creates a new resource/object with the provided data.
        
        Calls ``obj_create`` with the provided data and returns a response
        with the new resource's location.
        
        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        data = {}
        
        for key, value in deserialized.items():
            data[str(key)] = value
        
        bundle = self.build_bundle(data=data)
        updated_bundle = self.obj_create(bundle)
        return HttpCreated(location=self.get_resource_uri(updated_bundle))
    
    def post_detail(self, request, **kwargs):
        """
        Creates a new subcollection of the resource under a resource.
        
        This is not implemented by default because most people's data models
        aren't self-referential.
        
        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        return HttpNotImplemented()
    
    def delete_list(self, request, **kwargs):
        """
        Destroys a collection of resources/objects.
        
        Calls ``obj_delete_list``.
        
        If the resources are deleted, return ``HttpAccepted`` (204 No Content).
        """
        self.obj_delete_list(**self.remove_api_resource_names(kwargs))
        return HttpAccepted()
    
    def delete_detail(self, request, **kwargs):
        """
        Destroys a single resource/object.
        
        Calls ``obj_delete``.
        
        If the resource is deleted, return ``HttpAccepted`` (204 No Content).
        If the resource did not exist, return ``HttpGone`` (410 Gone).
        """
        try:
            self.obj_delete(**self.remove_api_resource_names(kwargs))
            return HttpAccepted()
        except NotFound:
            return HttpGone()
    
    def get_schema(self, request, **kwargs):
        """
        Returns a serialized form of the schema of the resource.
        
        Calls ``build_schema`` to generate the data. This method only responds
        to HTTP GET.
        
        Should return a HttpResponse (200 OK).
        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)
        self.log_throttled_access(request)
        return self.create_response(request, self.build_schema())
    
    def get_multiple(self, request, **kwargs):
        """
        Returns a serialized list of resources based on the identifers
        from the URL.
        
        Calls ``obj_get`` to fetch only the objects requested. This method
        only responds to HTTP GET.
        
        Should return a HttpResponse (200 OK).
        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)
        
        # Rip apart the list then iterate.
        obj_pks = kwargs.get('pk_list', '').split(';')
        objects = []
        not_found = []
        
        for pk in obj_pks:
            try:
                obj = self.obj_get(pk=pk)
                bundle = self.full_dehydrate(obj)
                objects.append(bundle)
            except ObjectDoesNotExist:
                not_found.append(pk)
        
        object_list = {
            'objects': objects,
        }
        
        if len(not_found):
            object_list['not_found'] = not_found
        
        self.log_throttled_access(request)
        return self.create_response(request, object_list)


class ModelDeclarativeMetaclass(DeclarativeMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(ModelDeclarativeMetaclass, cls).__new__(cls, name, bases, attrs)
        fields = getattr(new_class._meta, 'fields', [])
        excludes = getattr(new_class._meta, 'excludes', [])
        field_names = new_class.base_fields.keys()
        
        for field_name in field_names:
            if field_name == 'resource_uri':
                continue
            if field_name in new_class.declared_fields:
                continue
            if len(fields) and not field_name in fields:
                del(new_class.base_fields[field_name])
            if len(excludes) and field_name in excludes:
                del(new_class.base_fields[field_name])
        
        # Add in the new fields.
        new_class.base_fields.update(new_class.get_fields(fields, excludes))
        
        if getattr(new_class._meta, 'include_absolute_url', True):
            if not 'absolute_url' in new_class.base_fields:
                new_class.base_fields['absolute_url'] = CharField(attribute='get_absolute_url', readonly=True)
        elif 'absolute_url' in new_class.base_fields and not 'absolute_url' in attrs:
            del(new_class.base_fields['absolute_url'])
        
        return new_class


class ModelResource(Resource):
    """
    A subclass of ``Resource`` designed to work with Django's ``Models``.
    
    This class will introspect a given ``Model`` and build a field list based
    on the fields found on the model (excluding relational fields).
    
    Given that it is aware of Django's ORM, it also handles the CRUD data
    operations of the resource.
    """
    __metaclass__ = ModelDeclarativeMetaclass
    
    @classmethod
    def should_skip_field(cls, field):
        """
        Given a Django model field, return if it should be included in the
        contributed ApiFields.
        """
        # Ignore certain fields (related fields).
        if getattr(field, 'rel'):
            return True
        
        return False
    
    @classmethod
    def api_field_from_django_field(cls, f, default=CharField):
        """
        Returns the field type that would likely be associated with each
        Django type.
        """
        result = default
        
        if f.get_internal_type() in ('DateField', 'DateTimeField'):
            result = DateTimeField
        elif f.get_internal_type() in ('BooleanField', 'NullBooleanField'):
            result = BooleanField
        elif f.get_internal_type() in ('DecimalField', 'FloatField'):
            result = FloatField
        elif f.get_internal_type() in ('IntegerField', 'PositiveIntegerField', 'PositiveSmallIntegerField', 'SmallIntegerField'):
            result = IntegerField
        elif f.get_internal_type() in ('FileField', 'ImageField'):
            result = FileField
        # TODO: Perhaps enable these via introspection. The reason they're not enabled
        #       by default is the very different ``__init__`` they have over
        #       the other fields.
        # elif f.get_internal_type() == 'ForeignKey':
        #     result = ForeignKey
        # elif f.get_internal_type() == 'ManyToManyField':
        #     result = ManyToManyField
    
        return result
    
    @classmethod
    def get_fields(cls, fields=None, excludes=None):
        """
        Given any explicit fields to include and fields to exclude, add
        additional fields based on the associated model.
        """
        final_fields = {}
        fields = fields or []
        excludes = excludes or []
        
        if not cls._meta.object_class:
            return final_fields
        
        for f in cls._meta.object_class._meta.fields:
            # If the field name is already present, skip
            if f.name in cls.base_fields:
                continue
            
            # If field is not present in explicit field listing, skip
            if fields and f.name not in fields:
                continue
            
            # If field is in exclude list, skip
            if excludes and f.name in excludes:
                continue
            
            if cls.should_skip_field(f):
                continue
            
            api_field_class = cls.api_field_from_django_field(f)
            
            kwargs = {
                'attribute': f.name,
            }
            
            if f.null is True:
                kwargs['null'] = True

            kwargs['unique'] = f.unique
            
            if not f.null and f.blank is True:
                kwargs['default'] = ''
            
            if f.get_internal_type() == 'TextField':
                kwargs['default'] = ''
            
            if f.has_default():
                kwargs['default'] = f.default
            
            final_fields[f.name] = api_field_class(**kwargs)
            final_fields[f.name].instance_name = f.name
        
        return final_fields
    
    def build_filters(self, filters=None):
        """
        Given a dictionary of filters, create the necessary ORM-level filters.
        
        Keys should be resource fields, **NOT** model fields.
        
        Valid values are either a list of Django filter types (i.e.
        ``['startswith', 'exact', 'lte']``), the ``ALL`` constant or the
        ``ALL_WITH_RELATIONS`` constant.
        """
        # At the declarative level:
        #     filtering = {
        #         'resource_field_name': ['exact', 'startswith', 'endswith', 'contains'],
        #         'resource_field_name_2': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        #         'resource_field_name_3': ALL,
        #         'resource_field_name_4': ALL_WITH_RELATIONS,
        #         ...
        #     }
        # Accepts the filters as a dict. None by default, meaning no filters.
        if filters is None:
            filters = {}
        
        qs_filters = {}
        
        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            
            if not filter_bits[0] in self.fields:
                # It's not a field we know about. Move along citizen.
                continue
            
            if not filter_bits[0] in self._meta.filtering:
                raise InvalidFilterError("The '%s' field does not allow filtering." % filter_bits[0])
            
            if filter_bits[-1] in QUERY_TERMS.keys():
                filter_type = filter_bits.pop()
            else:
                filter_type = 'exact'
            
            # Check to see if it's allowed lookup type.
            if not self._meta.filtering[filter_bits[0]] in (ALL, ALL_WITH_RELATIONS):
                # Must be an explicit whitelist.
                if not filter_type in self._meta.filtering[filter_bits[0]]:
                    raise InvalidFilterError("'%s' is not an allowed filter on the '%s' field." % (filter_expr, filter_bits[0]))
            
            # Check to see if it's a relational lookup and if that's allowed.
            if len(filter_bits) > 1:
                if not self._meta.filtering[filter_bits[0]] == ALL_WITH_RELATIONS:
                    raise InvalidFilterError("Lookups are not allowed more than one level deep on the '%s' field." % filter_bits[0])
            
            if self.fields[filter_bits[0]].attribute is None:
                raise InvalidFilterError("The '%s' field has no 'attribute' for searching with." % filter_bits[0])
            
            if value == 'true':
                value = True
            elif value == 'false':
                value = False
            elif value in ('nil', 'none', 'None'):
                value = None
            
            db_field_name = LOOKUP_SEP.join([self.fields[filter_bits[0]].attribute] + filter_bits[1:])
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value
        
        return dict_strip_unicode_keys(qs_filters)
    
    def apply_sorting(self, obj_list, options=None):
        """
        Given a dictionary of options, apply some ORM-level sorting to the
        provided ``QuerySet``.
        
        Looks for the ``sort_by`` key and handles either ascending (just the
        field name) or descending (the field name with a ``-`` in front).
        
        The field name should be the resource field, **NOT** model field.
        """
        if options is None:
            options = {}
        
        if not 'sort_by' in options:
            # Nothing to alter the sort order. Return what we've got.
            return obj_list
        
        sort_by_bits = options['sort_by'].split(LOOKUP_SEP)
        field_name = sort_by_bits[0]
        order = ''
        
        if sort_by_bits[0].startswith('-'):
            field_name = sort_by_bits[0][1:]
            order = '-'
        
        if not field_name in self.fields:
            # It's not a field we know about. Move along citizen.
            raise InvalidSortError("No matching '%s' field for ordering on." % field_name)
        
        if not field_name in self._meta.ordering:
            raise InvalidSortError("The '%s' field does not allow ordering." % field_name)
        
        if self.fields[field_name].attribute is None:
            raise InvalidSortError("The '%s' field has no 'attribute' for ordering with." % field_name)
        
        sort_expr = "%s%s" % (order, LOOKUP_SEP.join([self.fields[field_name].attribute] + sort_by_bits[1:]))
        return obj_list.order_by(sort_expr)
    
    def obj_get_list(self, filters=None, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_list``.
        
        Takes an optional ``filters`` dictionary, which can be used to narrow
        the query.
        """
        applicable_filters = self.build_filters(filters)
        
        try:
            return self._meta.queryset.filter(**applicable_filters)
        except ValueError, e:
            raise NotFound("Invalid resource lookup data provided (mismatched type).")
    
    def obj_get(self, **kwargs):
        """
        A ORM-specific implementation of ``obj_get``.
        
        Takes optional ``kwargs``, which are used to narrow the query to find
        the instance.
        """
        try:
            return self._meta.queryset.get(**kwargs)
        except ValueError, e:
            raise NotFound("Invalid resource lookup data provided (mismatched type).")
    
    def obj_create(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_create``.
        """
        bundle.obj = self._meta.object_class()
        
        for key, value in kwargs.items():
            setattr(bundle.obj, key, value)
        
        bundle = self.full_hydrate(bundle)
        bundle.obj.save()
        
        # Now pick up the M2M bits.
        m2m_bundle = self.hydrate_m2m(bundle)
        self.save_m2m(m2m_bundle)
        return bundle
    
    def obj_update(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_update``.
        """
        if not bundle.obj or not bundle.obj.pk:
            # Attempt to hydrate data from kwargs before doing a lookup for the object.
            # This step is needed so certain values (like datetime) will pass model validation.
            try:
                bundle.obj = self._meta.queryset.model()
                bundle.data.update(kwargs)
                bundle = self.full_hydrate(bundle)
                lookup_kwargs = kwargs.copy()
                lookup_kwargs.update(dict(
                    (k, getattr(bundle.obj, k))
                    for k in kwargs.keys()
                    if getattr(bundle.obj, k) is not None))
            except:
                # if there is trouble hydrating the data, fall back to just
                # using kwargs by itself (usually it only contains a "pk" key
                # and this will work fine.
                lookup_kwargs = kwargs
            try:
                bundle.obj = self._meta.queryset.get(**lookup_kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")
        
        bundle = self.full_hydrate(bundle)
        bundle.obj.save()
        
        # Now pick up the M2M bits.
        m2m_bundle = self.hydrate_m2m(bundle)
        self.save_m2m(m2m_bundle)
        return bundle
    
    def obj_delete_list(self, **kwargs):
        """
        A ORM-specific implementation of ``obj_delete_list``.
        
        Takes optional ``kwargs``, which can be used to narrow the query.
        """
        self._meta.queryset.filter(**kwargs).delete()
    
    def obj_delete(self, **kwargs):
        """
        A ORM-specific implementation of ``obj_delete``.
        
        Takes optional ``kwargs``, which are used to narrow the query to find
        the instance.
        """
        try:
            obj = self._meta.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise NotFound("A model instance matching the provided arguments could not be found.")
        
        obj.delete()
    
    def save_m2m(self, bundle):
        """
        Handles the saving of related M2M data.
        
        Due to the way Django works, the M2M data must be handled after the
        main instance, which is why this isn't a part of the main ``save`` bits.
        
        Currently slightly inefficient in that it will clear out the whole
        relation and recreate the related data as needed.
        """
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_m2m', False):
                continue
            
            if not field_object.attribute:
                continue
            
            # Get the manager.
            related_mngr = getattr(bundle.obj, field_object.attribute)
            
            if hasattr(related_mngr, 'clear'):
                # Clear it out, just to be safe.
                related_mngr.clear()
            
            related_objs = []
            
            for related_bundle in bundle.data[field_name]:
                related_bundle.obj.save()
                related_objs.append(related_bundle.obj)
            
            related_mngr.add(*related_objs)
    
    def get_resource_uri(self, bundle_or_obj):
        """
        Handles generating a resource URI for a single resource.
        
        Uses the model's ``pk`` in order to create the URI.
        """
        kwargs = {
            'resource_name': self._meta.resource_name,
        }
        
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.pk
        else:
            kwargs['pk'] = bundle_or_obj.id
        
        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name
        
        return reverse("api_dispatch_detail", kwargs=kwargs)


# Based off of ``piston.utils.coerce_put_post``. Similarly BSD-licensed.
# And no, the irony is not lost on me.
def convert_post_to_put(request):
    """
    Force Django to process the PUT.
    """
    if request.method == "PUT":
        if hasattr(request, '_post'):
            del request._post
            del request._files
        
        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = "PUT"
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'
            
        request.PUT = request.POST
    
    return request
