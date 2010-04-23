from tastypie.fields import CharField
from tastypie.representations.models import ModelRepresentation
from basic.models import Note
 
 
class NoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.all()
