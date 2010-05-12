from django.contrib.auth.models import User
from tastypie.fields import CharField, ForeignKey
from tastypie.resources import ModelResource
from basic.models import Note


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()


class NoteResource(ModelResource):
    user = ForeignKey(UserResource, 'user')
    
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
