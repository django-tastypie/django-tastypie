from django.conf.urls.defaults import *
from tastypie.api import Api
from inherited_models.api.resources import ProductResource

api = Api(api_name='v1')
api.register(ProductResource(), canonical=True)

urlpatterns = api.urls
