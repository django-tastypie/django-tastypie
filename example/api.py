import datetime
from tastypie.http import HttpForbidden
from tastypie.resources import Resource
from tastypie.representations import ModelRepresentation
from example.models import Note


class NoteRepresentation(ModelRepresentation):
    class Meta:
        model = Note


class NoteResource(Resource):
    representation_class = NoteRepresentation
    allowed_methods = ['get', 'put', 'post']
    
    # Override the default put by doing a timestamp check
    def put_detail(request, obj_id):
        obj = self.representation.get(obj_id)
        
        # Custom logic.
        now = datetime.datetime.now()
        editable_before = now - datetime.timedelta(hours=1)
        
        if obj.created < editable_before:
            return HttpForbidden("That resource is no longer editable.")
        
        resource = self.representation.read(obj)
        return HttpResponse(content=self.serializer.write(resource), content_type=self.serializer.content_type)
        