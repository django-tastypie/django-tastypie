from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from core.models import MediaBit, Note


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        allowed_methods = ['get',]


class NoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author')
    
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()
        # this nested resource also should be updated when 
        # the mediabit resource will be updated
        allowed_methods = ['get', 'post', 'put', 'delete']


class MediaBitFullResource(ModelResource):
    note = fields.ForeignKey(NoteResource, 'note', full=True)

    class Meta:
        resource_name = 'mediabit-full'
        queryset = MediaBit.objects.all()
        authorization = Authorization()
