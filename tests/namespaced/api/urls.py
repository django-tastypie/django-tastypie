from django.conf import settings
from django.urls.conf import include, re_path
from tastypie.api import NamespacedApi
from namespaced.api.resources import NamespacedNoteResource, NamespacedUserResource


api = NamespacedApi(api_name='v1', urlconf_namespace='special')
api.register(NamespacedNoteResource(), canonical=True)
api.register(NamespacedUserResource(), canonical=True)

if settings.DJANGO_VERSION >= settings.DJANGO_19:
    included = include((api.urls, 'special'))
else:
    included = include(api.urls, namespace='special')

urlpatterns = [
    re_path(r'^api/', included),
]
