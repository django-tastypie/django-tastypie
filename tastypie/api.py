from django.conf.urls.defaults import *
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from tastypie.exceptions import TastyPieError, NotRegistered
from tastypie.serializers import Serializer


class Api(object):
    """
    Implements a registry to tie together the various resources that make up
    an API.
    
    Especially useful for navigation, HATEOAS and for providing multiple
    versions of your API.
    """
    def __init__(self, api_name="v1"):
        self.api_name = api_name
        self._registry = {}
        self._canonicals = {}
    
    def register(self, resource, canonical=False):
        resource_name = getattr(resource, 'resource_name', None)
        
        if resource_name is None:
            raise ImproperlyConfigured("Resource %r must define a 'resource_name'." % resource)
        
        self._registry[resource_name] = resource
        
        if canonical is True:
            self._canonicals[resource_name] = resource
    
    def unregister(self, resource_name):
        if resource_name in self._registry:
            del(self._registry[resource_name])
        
        if resource_name in self._canonicals:
            del(self._canonicals[resource_name])
    
    def canonical_resource_for(self, resource_name):
        if resource_name in self._canonicals:
            return self._canonicals[resource_name]
        
        raise NotRegistered("No resource was registered as canonical for '%s'." % resource_name)
    
    def wrap_view(self, view):
        def wrapper(request, *args, **kwargs):
            return getattr(self, view)(request, *args, **kwargs)
        return wrapper
    
    @property
    def urls(self):
        pattern_list = [
            url(r"^(?P<api_name>%s)/$" % self.api_name, self.wrap_view('top_level'), name="api_%s_top_level" % self.api_name),
        ]
        
        for name in sorted(self._registry.keys()):
            self._registry[name].api_name = self.api_name
            pattern_list.append((r"^(?P<api_name>%s)/" % self.api_name, include(self._registry[name].urls)))
        
        urlpatterns = patterns('',
            *pattern_list
        )
        return urlpatterns
    
    def top_level(self, request, api_name=None):
        # FIXME: api_name is never handled here but is captured in the urlpattern above.
        # FIXME: Hard-coding this sucks but there's logic in ``Resource`` that
        #        covers this behavior. Abstraction is needed.
        serializer = Serializer()
        available_resources = {}
        
        for name in sorted(self._registry.keys()):
            available_resources[name] = reverse("api_dispatch_list", kwargs={
                'api_name': self.api_name,
                'resource_name': name,
            })
        
        serialized = serializer.to_json(available_resources)
        return HttpResponse(content=serialized, content_type='application/json; charset=utf-8')
