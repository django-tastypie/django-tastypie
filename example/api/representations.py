from tastypie.representations.models import ModelRepresentation
from notes.models import Note
 
 
class NoteRepresentation(ModelRepresentation):
    resource_uri = CharField()
    
    class Meta:
        queryset = Note.objects.all()
    
    # FIXME: This should probably get significantly more automated.
    def dehydrate_resource_uri(self, obj):
        return self.get_resource_uri(obj)
