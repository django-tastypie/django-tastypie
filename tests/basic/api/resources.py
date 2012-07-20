from django.conf.urls.defaults import url
from django.contrib.auth.models import User
from tastypie.bundle import Bundle
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from basic.models import Note, AnnotatedNote, SlugBasedNote, RelatedBasedNote


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

    def create_response(self, *args, **kwargs):
        resp = super(CachedUserResource, self).create_response(*args, **kwargs)
        resp['Cache-Control'] = "max-age=3600"
        return resp


class NoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()


class AnnotatedNoteResource(ModelResource):
    class Meta:
        queryset = AnnotatedNote.objects.all()
        resource_name = 'annotatednotes'


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


class RelatedBasedNoteResource(ModelResource):
    note = fields.ForeignKey(AnnotatedNoteResource, 'note')

    class Meta:
        queryset = RelatedBasedNote.objects.all()
        resource_name = 'relatedbased'
        detail_uri_name = 'note__note__slug'
