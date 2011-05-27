from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from core.models import Note


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        allowed_methods = ['get']


class NoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author')
    
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()

