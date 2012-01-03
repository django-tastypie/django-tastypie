from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from basic.models import Note, AnnotatedNote


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


class BustedResource(ModelResource):
    class Meta:
        queryset = AnnotatedNote.objects.all()
        resource_name = 'busted'

    def get_list(self, *args, **kwargs):
        raise Exception("It's broke.")
