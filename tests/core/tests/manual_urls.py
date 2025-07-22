from django.urls import include, re_path as url
from core.tests.resources import NoteResource


note_resource = NoteResource()

urlpatterns = [
    url(r'^', include(note_resource.urls)),
]
