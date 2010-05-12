from django.conf.urls.defaults import *
from tastypie import fields
from tastypie.resources import ModelResource
from core.models import Note, Subject
from core.tests.api import Api, UserResource


class SubjectResource(ModelResource):
    class Meta:
        resource_name = 'subjects'
        queryset = Subject.objects.all()


class CustomNoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author')
    subjects = fields.ManyToManyField(SubjectResource, 'subjects')
    
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()


api = Api(api_name='v1')
api.register(CustomNoteResource())
api.register(UserResource())
api.register(SubjectResource())

urlpatterns = patterns('',
    (r'^api/', include(api.urls)),
)
