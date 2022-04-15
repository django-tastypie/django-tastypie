from django.urls.conf import include, re_path
from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from core.models import Note, Subject
from core.tests.api import Api


class SubjectResource(ModelResource):
    class Meta:
        resource_name = 'subjects'
        queryset = Subject.objects.all()


class UserResource(ModelResource):
    class Meta:
        resource_name = 'user'
        queryset = User.objects.all()


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

urlpatterns = [
    re_path(r'^api/', include(api.urls)),
]
