try:
    from django.conf.urls import patterns, include
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import patterns, include
from core.tests.resources import NoteResource


note_resource = NoteResource()

urlpatterns = patterns('',
    (r'^', include(note_resource.urls)),
)
