from django.conf.urls.defaults import patterns, url, include

from tastypie.api import Api
from .api.resources import ArticleResource
v1_api = Api()
v1_api.register(ArticleResource())


urlpatterns = patterns('',
    url(r'^api/', include(v1_api.urls)),
)
