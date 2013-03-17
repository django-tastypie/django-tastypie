try:
    from django.conf.urls import *
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import *
from tastypie.api import Api
from content_gfk.api.resources import NoteResource, QuoteResource, \
    RatingResource, DefinitionResource


api = Api(api_name='v1')
api.register(NoteResource())
api.register(QuoteResource())
api.register(RatingResource())
api.register(DefinitionResource())

urlpatterns = api.urls
