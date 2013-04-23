try:
    from django.conf.urls import patterns, include, url
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import patterns, include, url
from tastypie.api import NamespacedApi
from namespaced.api.resources import NamespacedNoteResource, NamespacedUserResource

api = NamespacedApi(api_name='v1', urlconf_namespace='special')
api.register(NamespacedNoteResource(), canonical=True)
api.register(NamespacedUserResource(), canonical=True)

urlpatterns = patterns('',
    url(r'^api/', include(api.urls, namespace='special')),
)
