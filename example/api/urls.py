from django.conf.urls.defaults import *
from api.resources import NoteResource
 
note_resource = NoteResource()
 
urlpatterns = patterns('',
    (r'^notes/', include(note_resource.urls)),
)
