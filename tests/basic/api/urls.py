from django.conf.urls.defaults import *
from tastypie.api import Api
from basic.api.resources import NoteResource, UserResource, BustedResource, CachedUserResource, SlugBasedNoteResource

api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)
api.register(CachedUserResource(), canonical=True)

v2_api = Api(api_name='v2')
v2_api.register(BustedResource(), canonical=True)
v2_api.register(SlugBasedNoteResource())

urlpatterns = v2_api.urls + api.urls
