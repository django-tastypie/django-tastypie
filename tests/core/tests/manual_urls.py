from django.conf.urls import include, url
from core.tests.resources import NoteResource


note_resource = NoteResource()

urlpatterns = [
    url(r'^', include(note_resource.urls)),
]
