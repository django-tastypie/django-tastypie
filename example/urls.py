from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Other app-specific views here.
    # Then...
    
    (r'^api/', include('api.urls')),
)