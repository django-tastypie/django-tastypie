from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie import fields
from tastypie.resources import ModelResource
from ..models import AuthorProfile, Article


class PerUserAuthorization(Authorization):
    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        return True

    def update_list(self, object_list, bundle):
        revised_list = []

        for article in object_list:
            for profile in article.authors.all():
                if bundle.request.user.pk == profile.user.pk:
                    revised_list.append(article)

        return revised_list

    def update_detail(self, object_list, bundle):
        if getattr(bundle.obj, 'pk', None):
            try:
                object_list.get(pk=bundle.obj.pk)

                for profile in bundle.obj.authors.all():
                    if bundle.request.user.pk == profile.user.pk:
                        return True
            except ObjectDoesNotExist:
                pass

        # Fallback on the data sent.
        for profile in bundle.data['authors']:
            if hasattr(profile, 'keys'):
                if bundle.request.user.pk == profile['user'].get('id'):
                    return True
            else:
                # Ghetto.
                if bundle.request.user.pk == profile.strip('/').split('/')[-1]:
                    return True

        raise Unauthorized("Nope.")

    def delete_list(self, object_list, bundle):
        # Disallow deletes completely.
        raise Unauthorized("Nope.")

    def delete_detail(self, object_list, bundle):
        # Disallow deletes completely.
        raise Unauthorized("Nope.")


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        authentication = BasicAuthentication()
        authorization = Authorization()
        excludes = ['email', 'password', 'is_staff', 'is_superuser']


class SiteResource(ModelResource):
    class Meta:
        queryset = Site.objects.all()
        authentication = BasicAuthentication()
        authorization = Authorization()


class AuthorProfileResource(ModelResource):
    user = fields.ToOneField(UserResource, 'user', full=True)
    sites = fields.ToManyField(SiteResource, 'sites', related_name='author_profiles', full=True)

    class Meta:
        queryset = AuthorProfile.objects.all()
        authentication = BasicAuthentication()
        authorization = Authorization()


class ArticleResource(ModelResource):
    authors = fields.ToManyField(AuthorProfileResource, 'authors', related_name='articles', full=True)

    class Meta:
        queryset = Article.objects.all()
        authentication = BasicAuthentication()
        authorization = PerUserAuthorization()
