try:
    from django.conf.urls import *
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import *
from tastypie.api import Api
from alphanumeric.api.resources import ProductResource

api = Api(api_name='v1')
api.register(ProductResource(), canonical=True)

urlpatterns = api.urls
