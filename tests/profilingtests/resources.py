from django.contrib.auth.models import User

from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource, ALL

from .models import Note


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        authorization = Authorization()


class NoteResource(ModelResource):
    author = fields.ToOneField(UserResource, 'author', full=True)

    class Meta:
        resource_name = 'notes'
        authorization = Authorization()
        filtering = {
            'content': ['startswith', 'exact'],
            'title': ALL,
            'slug': ['exact'],
        }
        ordering = ['title', 'slug', 'resource_uri']
        queryset = Note.objects.all()
