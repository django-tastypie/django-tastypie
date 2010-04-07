from django.conf.urls.defaults import *
from tastypie import fields
from tastypie.resources import Resource
from core.tests.api import Api, NoteResource, UserResource, NoteRepresentation
from core.tests.fields import UserRepresentation, SubjectRepresentation


class SubjectResource(Resource):
    representation = SubjectRepresentation
    resource_name = 'subjects'


class CustomNoteRepresentation(NoteRepresentation):
    author = fields.ForeignKey(UserRepresentation, 'author')
    subjects = fields.ManyToManyField(SubjectRepresentation, 'subjects')


api = Api(api_name='v1')
api.register(NoteResource(representation=CustomNoteRepresentation))
api.register(UserResource())
api.register(SubjectResource())

urlpatterns = patterns('',
    (r'^api/', include(api.urls)),
)
