from tastypie.resources import Resource
from basic.api.representations import NoteRepresentation
 
 
class NoteResource(Resource):
    representation = NoteRepresentation
    resource_name = 'notes'
