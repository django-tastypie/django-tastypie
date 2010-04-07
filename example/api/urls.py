from django.conf.urls.defaults import *
from tastypie.api import Api
from api.resources import NoteResource

api = Api(api_name='v1')
api.register(NoteResource())

urlpatterns = patterns('',
    (r'^', include(api.urls)),
)
