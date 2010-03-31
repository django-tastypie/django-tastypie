from tastypie.representations.models import ModelRepresentation
from notes.models import Note
 
 
class NoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.all()
    
    def get_resource_uri(self):
        return '/api/v1/notes/%s/' % self.instance.id
