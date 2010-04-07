from tastypie.representations.models import ModelRepresentation
from notes.models import Note
 
 
class NoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.all()
