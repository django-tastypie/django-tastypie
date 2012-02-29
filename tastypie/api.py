import warnings
from django.conf.urls.defaults import *
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from tastypie.exceptions import NotRegistered, BadRequest
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash, is_valid_jsonp_callback_value
from tastypie.utils.mime import determine_format, build_content_type


class Api(object):
    """
    Implements a registry to tie together the various resources that make up
    an API.

    Especially useful for navigation, HATEOAS and for providing multiple
    versions of your API.

    Optionally supplying ``api_name`` allows you to name the API. Generally,
    this is done with version numbers (i.e. ``v1``, ``v2``, etc.) but can
    be named any string.
    """
    def __init__(self, api_name="v1"):
        self.api_name = api_name
        self._api_name_accept_header = False
        self._reverse_url_prefix = '/'
        self._registry = {}
        self._canonicals = {}

    def register(self, resource, canonical=True):
        """
        Registers an instance of a ``Resource`` subclass with the API.

        Optionally accept a ``canonical`` argument, which indicates that the
        resource being registered is the canonical variant. Defaults to
        ``True``.
        """
        resource_name = getattr(resource._meta, 'resource_name', None)

        if resource_name is None:
            raise ImproperlyConfigured("Resource %r must define a 'resource_name'." % resource)

        self._registry[resource_name] = resource

        if canonical is True:
            if resource_name in self._canonicals:
                warnings.warn("A new resource '%r' is replacing the existing canonical URL for '%s'." % (resource, resource_name), Warning, stacklevel=2)

            self._canonicals[resource_name] = resource
            # TODO: This is messy, but makes URI resolution on FK/M2M fields
            #       work consistently.
            resource._meta.api_name = self.api_name
            resource._meta._api_name_accept_header = self._api_name_accept_header
            resource._meta._reverse_url_prefix = self._reverse_url_prefix
            resource.__class__.Meta.api_name = self.api_name

    def unregister(self, resource_name):
        """
        If present, unregisters a resource from the API.
        """
        if resource_name in self._registry:
            del(self._registry[resource_name])

        if resource_name in self._canonicals:
            del(self._canonicals[resource_name])

    def canonical_resource_for(self, resource_name):
        """
        Returns the canonical resource for a given ``resource_name``.
        """
        if resource_name in self._canonicals:
            return self._canonicals[resource_name]

        raise NotRegistered("No resource was registered as canonical for '%s'." % resource_name)

    def wrap_view(self, view):
        def wrapper(request, *args, **kwargs):
            return getattr(self, view)(request, *args, **kwargs)
        return wrapper

    def override_urls(self):
        """
        A hook for adding your own URLs or overriding the default URLs.
        """
        return []

    @property
    def urls(self):
        """
        Provides URLconf details for the ``Api`` and all registered
        ``Resources`` beneath it.
        """
        pattern_list = []
        if not self._api_name_accept_header:
            pattern_list = [
                url(r"^(?P<api_name>%s)%s$" % (self.api_name, trailing_slash()), self.wrap_view('top_level'), name="api_%s_top_level" % self.api_name),
            ]

        for name in sorted(self._registry.keys()):
            self._registry[name].api_name = self.api_name
            if self._api_name_accept_header:
                pattern_list.append(('', include(self._registry[name].urls)))
            else:
                pattern_list.append((r"^(?P<api_name>%s)/" % self.api_name, include(self._registry[name].urls)))

        urlpatterns = self.override_urls() + patterns('',
            *pattern_list
        )
        return urlpatterns

    def top_level(self, request, api_name=None):
        """
        A view that returns a serialized list of all resources registers
        to the ``Api``. Useful for discovery.
        """
        serializer = Serializer()
        available_resources = {}

        if api_name is None:
            api_name = self.api_name

        kwargs = {'resource_name': name}
        if not self._api_name_accept_header:
            kwargs['api_name'] = api_name

        for name in sorted(self._registry.keys()):
            available_resources[name] = {
                'list_endpoint': self._build_reverse_url("api_dispatch_list",
                    kwargs=kwargs),
                'schema': self._build_reverse_url("api_get_schema",
                    kwargs=kwargs),
            }

        desired_format = determine_format(request, serializer)
        options = {}

        if 'text/javascript' in desired_format:
            callback = request.GET.get('callback', 'callback')

            if not is_valid_jsonp_callback_value(callback):
                raise BadRequest('JSONP callback name is invalid.')

            options['callback'] = callback

        serialized = serializer.serialize(available_resources, desired_format, options)
        return HttpResponse(content=serialized, content_type=build_content_type(desired_format))

    def _build_reverse_url(self, name, args=None, kwargs=None):
        """
        A convenience hook for overriding how URLs are built.

        See ``NamespacedApi._build_reverse_url`` for an example.
        """
        path = reverse(name, urlconf=tuple(self.urls), args=args, kwargs=kwargs)
        return self._reverse_url_prefix + path[1:]


class NamespacedApi(Api):
    """
    An API subclass that respects Django namespaces.
    """
    def __init__(self, api_name="v1", urlconf_namespace=None):
        super(NamespacedApi, self).__init__(api_name=api_name)
        self.urlconf_namespace = urlconf_namespace

    def register(self, resource, canonical=True):
        super(NamespacedApi, self).register(resource, canonical=canonical)

        if canonical is True:
            # Plop in the namespace here as well.
            resource._meta.urlconf_namespace = self.urlconf_namespace

    def _build_reverse_url(self, name, args=None, kwargs=None):
        namespaced = "%s:%s" % (self.urlconf_namespace, name)
        path = reverse(namespaced, args=args, kwargs=kwargs)
        return self._reverse_url_prefix + path[1:]


class AcceptHeaderRouter(object):
    """
    Allows routing to different Api instances based on the HTTP Accept
    header.
    """
    # TODO write doc comment
    def __init__(self):
        self._registry = {}

    def register(self, api):
        """
        Registers an instance of an ``Api`` subclass.
        """
        api._api_name_accept_header = True
        self._registry[api.api_name] = api

    def unregister(self, api):
        """
        If present, unregisters an ``Api`` from the router.
        """
        self._registery.pop(api.api_name, None)

    def _api_name_from_headers(self):
        # XXX make this actually work.
        return 'v1'
    
    def api_from_headers(self):
        return self._registry[self._api_name_from_headers()]

    @property
    def urls(self):
        """
        Provides URLconf details for the ``Api`` and all registered
        ``Resources`` beneath it. Picks the correct ``Api`` based on
        the provided Accept header.
        """
        api_name = self._api_name_from_headers()
        return self._registry[api_name].urls

    def as_view(self):
        def view(request, *args, **kwargs):
            path = kwargs.values()[0]

            #############################
            ## This doesn't have to be in this method
            kwargs['rest'] = ''
            url_prefix = reverse(view, args=args, kwargs=kwargs)

            api = self.api_from_headers()
            api._reverse_url_prefix = url_prefix
            # Set the URL prefix for all Resources in this API
            for name in api._registry:
                api._registry[name]._meta._reverse_url_prefix = url_prefix
            #############################

            urls = patterns('',
                (r'', include(api.urls)))
            resolver = urls[0]

            func, args, kwargs = resolver.resolve(path)
            return func(request, *args, **kwargs)
        return view
