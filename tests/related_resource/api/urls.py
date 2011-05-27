from django.conf.urls.defaults import *
from tastypie.api import Api
from related_resource.api.resources import NoteResource, UserResource

api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)

urlpatterns = api.urls
