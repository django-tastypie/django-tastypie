from django.core.urls.defaults import *
from example.api import note_resource

urlpatterns = patterns('',
    # Other app-specific views here.
    # Then...
    
    (r'^api/', include(note_resource.get_urls)),
)