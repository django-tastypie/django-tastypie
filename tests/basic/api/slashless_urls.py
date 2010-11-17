from django.conf import settings
from django.conf.urls.defaults import *
from tastypie.api import Api
from basic.api.resources import NoteResource, UserResource

settings.APPEND_SLASH = False
settings.TASTYPIE_ALLOW_MISSING_SLASH = True

api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)

urlpatterns = patterns('',
    url(r'^api/', include(api.urls)),
)
