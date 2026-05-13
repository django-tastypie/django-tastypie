from django.urls.conf import include, re_path
from tastypie.api import Api
from slashless.api.resources import NoteResource, UserResource


api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)

urlpatterns = [
    re_path(r'^api/', include(api.urls)),
]
