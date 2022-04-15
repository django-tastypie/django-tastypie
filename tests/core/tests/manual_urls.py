from django.urls.conf import include, re_path
from core.tests.resources import NoteResource


note_resource = NoteResource()

urlpatterns = [
    re_path(r'^', include(note_resource.urls)),
]
