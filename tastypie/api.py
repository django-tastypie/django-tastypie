import warnings
import mimeparse
from django.conf.urls.defaults import *
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from tastypie.exceptions import NotRegistered, BadRequest
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash, is_valid_jsonp_callback_value
from tastypie.utils.mime import determine_format, build_content_type

# If ``csrf_exempt`` isn't present, stub it.
try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    def csrf_exempt(func):
        return func


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
        self._accept_header_routing = False
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
            resource.__class__.Meta.api_name = self.api_name
            resource._meta._api = self

        self._setup_accept_header(resource)

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
        Deprecated. Will be removed by v1.0.0. Please use ``prepend_urls`` instead.
        """
        warnings.warn("'override_urls' is a deprecated method & will be removed by v1.0.0. Please use ``prepend_urls`` instead.")
        return self.prepend_urls()

    def prepend_urls(self):
        """
        A hook for adding your own URLs or matching before the default URLs.
        """
        return []

    @property
    def urls(self):
        """
        Provides URLconf details for the ``Api`` and all registered
        ``Resources`` beneath it.
        """
        if not self._accept_header_routing:
            pattern_list = [
                url(r"^(?P<api_name>%s)%s$" % (self.api_name, trailing_slash()), self.wrap_view('top_level'), name="api_%s_top_level" % self.api_name),
            ]
        else:
            pattern_list = [
                url(r"^$", self.wrap_view('top_level'), name="api_%s_top_level" % self.api_name),
            ]

        for name in sorted(self._registry.keys()):
            self._registry[name].api_name = self.api_name
            if self._accept_header_routing:
                pattern_list.append(('', include(self._registry[name].urls)))
            else:
                pattern_list.append((r"^(?P<api_name>%s)/" % self.api_name, include(self._registry[name].urls)))

        urlpatterns = self.prepend_urls()

        if self.override_urls():
            warnings.warn("'override_urls' is a deprecated method & will be removed by v1.0.0. Please rename your method to ``prepend_urls``.")
            urlpatterns += self.override_urls()

        urlpatterns += patterns('',
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

        kwargs = {}
        if not self._accept_header_routing:
            kwargs['api_name'] = api_name

        for name in sorted(self._registry.keys()):
            kwargs['resource_name'] = name
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
        content_type = build_content_type(desired_format, api=self)
        return HttpResponse(content=serialized, content_type=content_type)

    def _build_reverse_url(self, name, args=None, kwargs=None):
        """
        A convenience hook for overriding how URLs are built.

        See ``NamespacedApi._build_reverse_url`` for an example.
        """
        urlconf = None
        if self._accept_header_routing:
            # We can't use the global urlconf for AcceptHeaderRouter
            # lookups.
            urlconf = tuple(self.urls)
        path = reverse(name, urlconf=urlconf, args=args, kwargs=kwargs)
        return self._reverse_url_prefix + path[1:]

    def _setup_accept_header(self, resource):
        resource._meta._accept_header_routing = self._accept_header_routing
        resource._meta._reverse_url_prefix = self._reverse_url_prefix


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
    header.  register() Api instances to allow routing.

    Routes to a given API based on application/vnd.api.<apiname>+<type>

    For instance, a request with:

    Accept: application/vnd.api.philip-v2+json

    would route to the API that's registered with the name "philip-v2".

    For requests with no name specified, we route to the Api instance that's
    registered with default=True
    """
    def __init__(self):
        self._registry = {}
        self._default_api_name = None

    def register(self, api, default=False):
        """
        Registers an instance of an ``Api`` subclass. If ``default`` is True
        then we will route to this Api instance when there's no api name
        specified.
        """
        api._accept_header_routing = True
        for api_name, resource in api._registry.iteritems():
            # Because a resource can be registered with an Api after the Api
            # has been registered with the AcceptHeaderRouter, we have
            # to do this when the Api itself is registered *and* when
            # the resource is registered with the Api.
            api._setup_accept_header(resource)
        self._registry[api.api_name] = api
        if default:
            self._default_api_name = api.api_name

    def unregister(self, api):
        """
        If present, unregisters an ``Api`` from the router.
        """
        self._registery.pop(api.api_name, None)

    def _api_name_from_headers(self, request):
        self._accept_range = request.META.get('HTTP_ACCEPT', '*/*')
        # Accepts header can look like:
        # text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
        # So we need to split it apart for use with parse_media_range.
        ranges = self._accept_range.split(',')
        ranges = [mimeparse.parse_media_range(m) for m in ranges]
        # Then sort the accepted types by their quality, best first.
        ranges.sort(
            lambda x, y: cmp(float(y[2].get('q')), float(x[2].get('q'))))
        for range in ranges:
            subtype = range[1]
            for api_name in self._registry.keys():
                # We enforce the vnd.api.<api_name>+<type> convention to keep
                # things simple.  E.g. vnd.api.myapi-v2+json or
                # vnd.api.djangoappv3+xml
                if subtype.startswith('vnd.api.%s+' % api_name):
                    # This is our match.
                    # Rewrite the Accepts header, removing our
                    # vendor-specific api name so that the rest of our logic
                    # works the same way.
                    request.META['HTTP_ACCEPT'] = self._accept_range.replace(
                        'vnd.api.%s+' % api_name, '')
                    return api_name

        return self._default_api_name

    def api_from_headers(self, request):
        return self._registry[self._api_name_from_headers(request)]

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
        @csrf_exempt
        def view(request, *args, **kwargs):
            path = kwargs.values()[0]

            kwargs['rest'] = ''
            url_prefix = reverse(view, args=args, kwargs=kwargs)

            api = self.api_from_headers(request)
            api._reverse_url_prefix = url_prefix
            # Set the URL prefix for all Resources in this API
            for name in api._registry:
                api._registry[name]._meta._reverse_url_prefix = url_prefix

            # Is it slow to do this? If so, we can pull out to an
            # instance variable.
            urls = patterns('',
                (r'', include(api.urls)))
            resolver = urls[0]

            func, args, kwargs = resolver.resolve(path)
            return func(request, *args, **kwargs)
        return view
