.. _ref-cookbook:

=================
Tastypie Cookbook
=================


Adding Custom Values
--------------------

You might encounter cases where you wish to include additional data in a
response which is not obtained from a field or method on your model. You can
easily extend the :meth:`~tastypie.resources.Resource.dehydrate` method to
provide additional values::

    class MyModelResource(Resource):
        class Meta:
            qs = MyModel.objects.all()

        def dehydrate(self, bundle):
            bundle.data['custom_field'] = "Whatever you want"
            return bundle


Pre-Request Alterations To The Queryset
---------------------------------------

A common pattern is needing to limit a queryset by something that changes
per-request, for instance the date/time. You can accomplish this by lightly
modifying ``get_object_list``::

    from tastypie.utils import now

    class MyResource(ModelResource):
        class Meta:
            queryset = MyObject.objects.all()

        def get_object_list(self, request):
            return super(MyResource, self).get_object_list(request).filter(start_date__gte=now)


Using Your ``Resource`` In Regular Views
----------------------------------------

In addition to using your resource classes to power the API, you can also use
them to write other parts of your application, such as your views. For
instance, if you wanted to encode user information in the page for some
Javascript's use, you could do the following::

    # views.py
    from django.shortcuts import render_to_response
    from myapp.api.resources import UserResource


    def user_detail(request, username):
        ur = UserResource()
        user = ur.obj_get(username=username)

        # Other things get prepped to go into the context then...

        ur_bundle = ur.build_bundle(obj=user, request=request)
        return render_to_response('myapp/user_detail.html', {
            # Other things here.
            "user_json": ur.serialize(None, ur.full_dehydrate(ur_bundle), 'application/json'),
        })


Using Non-PK Data For Your URLs
-------------------------------

By convention, ``ModelResource``s usually expose the detail endpoints utilizing
the primary key of the ``Model`` they represent. However, this is not a strict
requirement. Each URL can take other named URLconf parameters that can be used
for the lookup.

For example, if you want to expose ``User`` resources by username, you can do
something like the following::

    # myapp/api/resources.py
    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()

        def override_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<username>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

The added URLconf matches before the standard URLconf included by default &
matches on the username provided in the URL.


Nested Resources
----------------

You can also do "nested resources" (resources within another related resource)
by lightly overriding the ``override_urls`` method & adding on a new method to
handle the children::

    class ParentResource(ModelResource):
        children = fields.ToManyField(ChildResource, 'children')

        def override_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/children%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_children'), name="api_get_children"),
            ]

        def get_children(self, request, **kwargs):
            try:
                obj = self.cached_obj_get(request=request, **self.remove_api_resource_names(kwargs))
            except ObjectDoesNotExist:
                return HttpGone()
            except MultipleObjectsReturned:
                return HttpMultipleChoices("More than one resource is found at this URI.")

            child_resource = ChildResource()
            return child_resource.get_detail(request, parent_id=obj.pk)

Another alternative approach is to override the ``dispatch`` method::

    # myapp/api/resources.py
    class EntryResource(ModelResource):
        user = fields.ForeignKey(UserResource, 'user')

        class Meta:
            queryset = Entry.objects.all()
            resource_name = 'entry'

        def dispatch(self, request_type, request, **kwargs):
            username = kwargs.pop('username')
            kwargs['user'] = get_object_or_404(User, username=username)
            return super(EntryResource, self).dispatch(request_type, request, **kwargs)

    # urls.py
    from django.conf.urls.defaults import *
    from myapp.api import EntryResource

    entry_resource = EntryResource()

    urlpatterns = patterns('',
        # The normal jazz here, then...
        (r'^api/(?P<username>\w+)/', include(entry_resource.urls)),
    )


Adding Search Functionality
---------------------------

Another common request is being able to integrate search functionality. This
approach uses Haystack_, though you could hook it up to any search technology.
We leave the CRUD methods of the resource alone, choosing to add a new endpoint
at ``/api/v1/notes/search/``::

    from django.conf.urls.defaults import *
    from django.core.paginator import Paginator, InvalidPage
    from django.http import Http404
    from haystack.query import SearchQuerySet
    from tastypie.resources import ModelResource
    from tastypie.utils import trailing_slash
    from notes.models import Note


    class NoteResource(ModelResource):
        class Meta:
            queryset = Note.objects.all()
            resource_name = 'notes'

        def override_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            ]

        def get_search(self, request, **kwargs):
            self.method_check(request, allowed=['get'])
            self.is_authenticated(request)
            self.throttle_check(request)

            # Do the query.
            sqs = SearchQuerySet().models(Note).load_all().auto_query(request.GET.get('q', ''))
            paginator = Paginator(sqs, 20)

            try:
                page = paginator.page(int(request.GET.get('page', 1)))
            except InvalidPage:
                raise Http404("Sorry, no results on that page.")

            objects = []

            for result in page.object_list:
                bundle = self.build_bundle(obj=result.object, request=request)
                bundle = self.full_dehydrate(bundle)
                objects.append(bundle)

            object_list = {
                'objects': objects,
            }

            self.log_throttled_access(request)
            return self.create_response(request, object_list)

Alternately, in this recipe we leverage the Haystack ``SearchQuerySet`` API to expose documents from our search index themselves, vice piggy-backing on another resource for search functionality.::

    import operator
    
    from haystack.query import SearchQuerySet, SQ

    from tastypie import fields
    from tastypie.bundle import Bundle
    from tastypie.resources import Resource, ResourceOptions, DeclarativeMetaclass


    class SearchOptions(ResourceOptions):
        # One of the great strengths of Haystack is its extensibility. We have
        # subclassed many of Haystack's internal classes, including a subclass
        # of SearchQuerySet. I did not want to be locked in to using Haystack's
        # built-in SearchQuerySet nor its SQ object in this module, so I put in
        # the ``query_object`` attribute on the metaclass.
        resource_name = 'search'
        object_class = SearchQuerySet
        query_object = SQ
        index_fields = []
        # Override document_uid_field with whatever field in your index
        # you use to uniquely identify a single document. This value will be
        # used wherever the ModelResource references the ``pk`` kwarg.
        document_uid_field = 'id'
        lookup_sep = ','


    class SearchDeclarativeMetaclass(DeclarativeMetaclass):
        def __new__(cls, name, bases, attrs):
            new_class = super(SearchDeclarativeMetaclass, cls)\
                .__new__(cls, name, bases, attrs)
            opts = getattr(new_class, 'Meta', None)
            new_class._meta = SearchOptions(opts)
            include_fields = getattr(new_class._meta, 'fields', [])
            excludes = getattr(new_class._meta, 'excludes', [])
            field_names = new_class.base_fields.keys()

            for field_name in field_names:
                if field_name == 'resource_uri':
                    continue
                if field_name in new_class.declared_fields:
                    continue
                if len(include_fields) and not field_name in include_fields:
                    del(new_class.base_fields[field_name])
                if len(excludes) and field_name in excludes:
                    del(new_class.base_fields[field_name])

            if getattr(new_class._meta, 'include_absolute_url', True):
                if not 'absolute_url' in new_class.base_fields:
                    new_class.base_fields['absolute_url'] = fields.CharField(
                        attribute='get_absolute_url', readonly=True)
            elif 'absolute_url' in new_class.base_fields and not 'absolute_url' in attrs:
                del(new_class.base_fields['absolute_url'])

            return new_class


    class SearchResource(Resource):
        """
        Blueprint for implementing an HTTP API to access documents in a
        search engine via Haystack. The design of the class adds some
        additional configuration overhead (i.e. a handful of metaclass
        fields) in exchange for flexibility & portability.

        To implement this class in your own application, you will need to:
        1. Define which fields to return in your results;
        2. Override index_fields in the metaclass to limit or expand which
           fields consumers can access from your index via the API;
        3. Override document_uid_field in the metaclass to specify which
           field in the index is used to uniquely identify individual
           documents;
        4. Additionally, you will override query_object and object_class to
           utilize any subclasses you may be using in your project.

        """
        __metaclass__ = SearchDeclarativeMetaclass

        def apply_filters(self, request, applicable_filters):
            objects = self.get_object_list(request)

            if applicable_filters:
                return objects.filter(applicable_filters)
            else:
                return objects

        def build_filters(self, filters=None):
            """
            Create a single SQ filter from querystring parameters that
            correspond to SearchIndex fields that have been "registered" in
            the ``self._meta.index_fields``.

            Default behavior is to ``OR`` terms for the same parameter, and
            ``AND`` between parameters. For example:

            ``?format=json&state_exact=Indiana,Illinois&company_exact=IBM``

            would yield an SQ expressing the following logic:

            ``q=state_exact:(Indiana OR Illinois) AND company_exact:IBM``

            Any querystring parameters that are not registered in
            self._meta.index_fields and are not consumed elsewhere in the
            response operation will be ignored.

            """
            terms = []

            if filters is None:
                filters = {}

            for param, value in filters.items():

                if param not in self._meta.index_fields:
                    continue

                tokens = value.split(self._meta.lookup_sep)
                field_queries = []

                for token in tokens:

                    if token:
                        field_queries.append(self._meta.query_object((param,
                                                                      token)))

                terms.append(reduce(operator.or_,
                                    filter(lambda x: x, field_queries)))

            if terms:
                return reduce(operator.and_, filter(lambda x: x, terms))
            else:
                return terms

        def get_resource_uri(self, bundle_or_obj):
            """
            Generate direct link to individual document in our datastore.

            """
            kwargs = {
                'resource_name': self._meta.resource_name
            }
            uid = self._meta.document_uid_field

            if isinstance(bundle_or_obj, Bundle):
                kwargs['pk'] = getattr(bundle_or_obj.obj, uid, '')
            else:
                kwargs['pk'] = getattr(bundle_or_obj, uid, '')

            if self._meta.api_name is not None:
                kwargs['api_name'] = self._meta.api_name

            return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

        def get_object_list(self, request):
            """
            A Haystack-specific implementation of ``get_object_list``.

            Returns a SearchQuerySet that may have been limited by other
            filter/narrow/etc. operations.

            """
            return self._meta.object_class()._clone()

        def obj_get_list(self, request=None, **kwargs):
            filters = {}

            if hasattr(request, 'GET'):
                filters = request.GET.copy()

            filters.update(kwargs)
            applicable_filters = self.build_filters(filters=filters)
            return self.apply_filters(request, applicable_filters)

        def obj_get(self, request=None, **kwargs):
            """
            Fetch a single document from the datastore according to whatever
            unique identifier is available for that document in the
            SearchIndex.

            """
            # Don't let the use of 'pk' here and throughout confuse you.
            # Think of it as a metaphor standing for "whatever field there
            # is in your SearchIndex that uniquely identifies a single
            # document."
            doc_uid = kwargs.get('pk')
            uid_field = self._meta.document_uid_field
            sqs = self.get_object_list(request)

            if doc_uid:
                sqs = sqs.filter(self._meta.query_object((uid_field, doc_uid)))

                if sqs:
                    return sqs[0]
                else:
                    return sqs
                        


.. _Haystack: http://haystacksearch.org/


Creating per-user resources
---------------------------

One might want to create an API which will require every user to authenticate
and every user will be working only with objects associated with them. Let's see
how to implement it for two basic operations: listing and creation of an object.

For listing we want to list only objects for which 'user' field matches
'request.user'. This could be done by applying a filter in the ``apply_authorization_limits``
method of your resource.

For creating we'd have to wrap ``obj_create`` method of ``ModelResource``. Then the
resulting code will look something like::

    # myapp/api/resources.py
    class EnvironmentResource(ModelResource):
        class Meta:
            queryset = Environment.objects.all()
            resource_name = 'environment'
            list_allowed_methods = ['get', 'post']
            authentication = ApiKeyAuthentication()
            authorization = Authorization()

        def obj_create(self, bundle, request=None, **kwargs):
            return super(EnvironmentResource, self).obj_create(bundle, request, user=request.user)

        def apply_authorization_limits(self, request, object_list):
            return object_list.filter(user=request.user)

camelCase JSON Serialization
----------------------------

The convention in the world of Javascript has standardized on camelCase,
where Tastypie uses underscore syntax, which can lead to "ugly" looking
code in Javascript. You can create a custom serializer that emits
values in camelCase instead::

    from tastypie.serializers import Serializer

    class CamelCaseJSONSerializer(Serializer):
        formats = ['json']
        content_types = {
            'json': 'application/json',
        }

        def to_json(self, data, options=None):
            # Changes underscore_separated names to camelCase names to go from python convention to javacsript convention
            data = self.to_simple(data, options)

            def underscoreToCamel(match):
                return match.group()[0] + match.group()[2].upper()

            def camelize(data):
                if isinstance(data, dict):
                    new_dict = {}
                    for key, value in data.items():
                        new_key = re.sub(r"[a-z]_[a-z]", underscoreToCamel, key)
                        new_dict[new_key] = camelize(value)
                    return new_dict
                if isinstance(data, (list, tuple)):
                    for i in range(len(data)):
                        data[i] = camelize(data[i])
                    return data
                return data

            camelized_data = camelize(data)

            return simplejson.dumps(camelized_data, sort_keys=True)

        def from_json(self, content):
            # Changes camelCase names to underscore_separated names to go from javascript convention to python convention
            data = simplejson.loads(content)

            def camelToUnderscore(match):
                return match.group()[0] + "_" + match.group()[1].lower()

            def underscorize(data):
                if isinstance(data, dict):
                    new_dict = {}
                    for key, value in data.items():
                        new_key = re.sub(r"[a-z][A-Z]", camelToUnderscore, key)
                        new_dict[new_key] = underscorize(value)
                    return new_dict
                if isinstance(data, (list, tuple)):
                    for i in range(len(data)):
                        data[i] = underscorize(data[i])
                    return data
                return data

        underscored_data = underscorize(data)

        return underscored_data

Determining format via URL
--------------------------

Sometimes it's required to allow selecting the response format by
specifying it in the API URL, for example ``/api/v1/users.json`` instead
of ``/api/v1/users/?format=json``. The following snippet allows that kind
of syntax additional to the default URL scheme::

    # myapp/api/resources.py
    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()

        def override_urls(self):
            """
            Returns a URL scheme based on the default scheme to specify
            the response format as a file extension, e.g. /api/v1/users.json
            """
            return [
                url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
                url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
                url(r"^(?P<resource_name>%s)/set/(?P<pk_list>\w[\w/;-]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
                url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

        def determine_format(self, request):
            """
            Used to determine the desired format from the request.format
            attribute.
            """
            if (hasattr(request, 'format') and
                    request.format in self._meta.serializer.formats):
                return self._meta.serializer.get_mime_for_format(request.format)
            return super(UserResource, self).determine_format(request)

        def wrap_view(self, view):
            def wrapper(request, *args, **kwargs):
                request.format = kwargs.pop('format', None)
                wrapped_view = super(UserResource, self).wrap_view(view)
                return wrapped_view(request, *args, **kwargs)
            return wrapper
