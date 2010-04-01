from django.conf.urls.defaults import *
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from tastypie.exceptions import TastyPieError
from tastypie.serializers import Serializer


class Api(object):
    """
    Implements a registry to tie together the various resources that make up
    an API.
    
    Especially useful for navigation, HATEOAS and for providing multiple
    versions of your API.
    """
    def __init__(self, api_prefix=None):
        self.api_prefix = api_prefix
        self._registry = {}
        self._canonicals = {}
    
    def register(self, resource, url_prefix=None, canonical=False):
        if url_prefix is None:
            if not getattr(resource, 'url_prefix', None):
                raise ImproperlyConfigured("No url_prefix found for %r." % resource)
            
            url_prefix = getattr(resource, 'url_prefix', None)
        
        # If it's been custom-specified, let it override.
        if url_prefix != resource.url_prefix:
            resource.url_prefix = url_prefix
        
        self._registry[url_prefix] = resource
        
        # FIXME: Not sure about this yet.
        # if canonical is True:
        #     self._canonicals[url_prefix] = resource
    
    def unregister(self, url_prefix):
        if url_prefix in self._registry:
            del(self._registry[url_prefix])
            return True
        
        return False
    
    def wrap_view(self, view):
        def wrapper(request, *args, **kwargs):
            return getattr(self, view)(request, *args, **kwargs)
        return wrapper
    
    @property
    def urls(self):
        # FIXME: With multiple instances, you'll get ``name`` collisions.
        #        Need to propogate the ``api_prefix`` down to the individual
        #        patterns, which might hurt a bit.
        pattern_list = [
            url(r'^$', self.wrap_view('top_level'), name='api_top_level'),
        ]
        
        for prefix in sorted(self._registry.keys()):
            pattern_list.append(("^%s/" % prefix, include(self._registry[prefix].urls)))
        
        urlpatterns = patterns('',
            *pattern_list
        )
        return urlpatterns
    
    def top_level(self, request):
        # FIXME: Hard-coding this sucks but there's logic in ``Resource`` that
        #        covers this behavior. Abstraction is needed.
        serializer = Serializer()
        available_resources = {}
        
        for prefix in sorted(self._registry.keys()):
            available_resources[prefix] = reverse('api_%s_dispatch_list' % self._registry[prefix].url_prefix)
        
        serialized = serializer.to_json(available_resources)
        return HttpResponse(content=serialized, content_type='application/json; charset=utf-8')
