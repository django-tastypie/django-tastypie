from tastypie.resources import Resource
from basic.api.representations import NoteRepresentation, UserRepresentation


class NoteResource(Resource):
    representation = NoteRepresentation
    resource_name = 'notes'


class UserResource(Resource):
    representation = UserRepresentation
    resource_name = 'users'
