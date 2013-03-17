try:
    from django.conf.urls import *
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import *
from tastypie.api import Api
from gis.api.resources import GeoNoteResource, UserResource

api = Api(api_name='v1')
api.register(GeoNoteResource())
api.register(UserResource())

urlpatterns = api.urls
