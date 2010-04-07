from tastypie.resources import Resource
from api.representations import NoteRepresentation
 
 
class NoteResource(Resource):
    representation = NoteRepresentation
    resource_name = 'notes'
