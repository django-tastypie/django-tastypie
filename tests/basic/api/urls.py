from django.conf.urls.defaults import *
from tastypie.api import Api
from basic.api.resources import NoteResource, UserResource, BustedResource

api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)

v2_api = Api(api_name='v2')
v2_api.register(BustedResource(), canonical=True)

urlpatterns = v2_api.urls + api.urls
