from django.urls import include, re_path as url
from tastypie.api import Api
from slashless.api.resources import NoteResource, UserResource


api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)

urlpatterns = [
    url(r'^api/', include(api.urls)),
]
