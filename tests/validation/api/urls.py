try:
    from django.conf.urls import patterns, include, url
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import patterns, include, url
from tastypie.api import Api
from validation.api.resources import NoteResource, UserResource, AnnotatedNoteResource

api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)
api.register(AnnotatedNoteResource(), canonical=True)

urlpatterns = patterns('',
    url(r'^api/', include(api.urls)),
)
