from django.urls import include, re_path as url

from tastypie.api import Api

from validation.api.resources import NoteResource, UserResource,\
    AnnotatedNoteResource


api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)
api.register(AnnotatedNoteResource(), canonical=True)

urlpatterns = [
    url(r'^api/', include(api.urls)),
]
