from django.conf.urls import url, include

from tastypie.api import Api

from .api.resources import ArticleResource, AuthorProfileResource, SiteResource, UserResource


v1_api = Api()
v1_api.register(ArticleResource())
v1_api.register(AuthorProfileResource())
v1_api.register(SiteResource())
v1_api.register(UserResource())

urlpatterns = [
    url(r'^api/', include(v1_api.urls)),
]
