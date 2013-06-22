try:
    from django.conf.urls import patterns, url, include
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import patterns, url, include

from tastypie.api import Api
from .api.resources import (
    ArticleResource,
    AuthorProfileResource,
    SiteResource,
    UserResource,
    ItemResource,
    ItemShopOwnerResource,
    ShopResource,
    AccountResource,
    UserFuncResource,
)

v1_api = Api()
v1_api.register(ArticleResource())
v1_api.register(AuthorProfileResource())
v1_api.register(SiteResource())
v1_api.register(UserResource())
v1_api.register(ItemResource())
v1_api.register(ItemShopOwnerResource())
v1_api.register(ShopResource())
v1_api.register(AccountResource())
v1_api.register(UserFuncResource())


urlpatterns = patterns('',
    url(r'^api/', include(v1_api.urls)),
)
