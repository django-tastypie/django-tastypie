from django.conf.urls.defaults import *
from tastypie.api import Api
from pull769.api.resources import SimpleResource, RelatedResource

api = Api(api_name='v1')
api.register(SimpleResource())
api.register(RelatedResource())

urlpatterns = api.urls
