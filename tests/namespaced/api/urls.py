from django.conf.urls import include, url
from tastypie.api import NamespacedApi
from namespaced.api.resources import NamespacedNoteResource, NamespacedUserResource


api = NamespacedApi(api_name='v1', urlconf_namespace='special')
api.register(NamespacedNoteResource(), canonical=True)
api.register(NamespacedUserResource(), canonical=True)

urlpatterns = [
    url(r'^api/', include(api.urls, namespace='special')),
]
