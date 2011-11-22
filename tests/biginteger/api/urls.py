from django.conf.urls.defaults import *
from tastypie.api import Api
from biginteger.api.resources import ProductResource

api = Api(api_name='v1')
api.register(ProductResource(), canonical=True)

urlpatterns = api.urls
