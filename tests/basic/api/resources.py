from django.contrib.auth.models import User
from django.conf.urls import url
from tastypie.cache import SimpleCache
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import Authorization
from basic.models import Note, AnnotatedNote, SlugBasedNote

from tastypie.utils import trailing_slash
from tastypie.constants import ALL


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        authorization = Authorization()


class CachedUserResource(ModelResource):
    class Meta:
        allowed_methods = ('get', )
        queryset = User.objects.all()
        resource_name = 'cached_users'
        cache = SimpleCache(timeout=3600)


class PublicCachedUserResource(ModelResource):
    class Meta:
        allowed_methods = ('get', )
        queryset = User.objects.all()
        resource_name = 'public_cached_users'
        cache = SimpleCache(timeout=3600, public=True)


class CacheDisabledUserResource(ModelResource):
    class Meta:
        allowed_methods = ('get', )
        queryset = User.objects.all()
        resource_name = 'cache_disabled_users'
        cache = SimpleCache(timeout=0)


class PrivateCachedUserResource(ModelResource):
    class Meta:
        allowed_methods = ('get', )
        queryset = User.objects.all()
        resource_name = 'private_cached_users'
        cache = SimpleCache(timeout=3600, private=True)


class NoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()
        filtering = {"id": ALL}

    def override_urls(self):
        return [url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/filterin%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_filterin'), name="api_get_filterin"),]

    def get_filterin(self, request, **kwargs):
        note_resource = NoteResource()
        # ids can actually be generated in a different way
        ids = ["1", "2"]
        return note_resource.get_list(request, id__in=ids)


class BustedResource(ModelResource):
    class Meta:
        queryset = AnnotatedNote.objects.all()
        resource_name = 'busted'

    def get_list(self, *args, **kwargs):
        raise Exception("It's broke.")


class SlugBasedNoteResource(ModelResource):
    class Meta:
        queryset = SlugBasedNote.objects.all()
        resource_name = 'slugbased'
        detail_uri_name = 'slug'
        authorization = Authorization()


class SessionUserResource(ModelResource):
    class Meta:
        resource_name = 'sessionusers'
        queryset = User.objects.all()
        authentication = SessionAuthentication()
        authorization = Authorization()
