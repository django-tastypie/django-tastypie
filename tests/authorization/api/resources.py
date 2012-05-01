from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from tastypie.authorization import Authorization
from tastypie import fields
from tastypie.resources import ModelResource
from ..models import AuthorProfile, Article


class PerUserAuthorization(Authorization):
    # FIXME: Implement this!
    pass


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        excludes = ['email', 'password', 'is_staff', 'is_superuser']


class SiteResource(ModelResource):
    class Meta:
        queryset = Site.objects.all()


class AuthorProfileResource(ModelResource):
    user = fields.ToOneField(UserResource, 'user', full=True)
    sites = fields.ToManyField(SiteResource, 'sites', related_name='author_profiles', full=True)

    class Meta:
        queryset = AuthorProfile.objects.all()


class ArticleResource(ModelResource):
    authors = fields.ToManyField(AuthorProfileResource, 'authors', related_name='articles', full=True)

    class Meta:
        queryset = Article.objects.all()

