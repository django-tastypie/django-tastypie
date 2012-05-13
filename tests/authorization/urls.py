from django.conf.urls.defaults import patterns, url, include

from tastypie.api import Api
from authorization.api.resources import UserResource, NoteResource
v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(NoteResource())


urlpatterns = patterns('',
    url(r'^api/', include(v1_api.urls)),
)
