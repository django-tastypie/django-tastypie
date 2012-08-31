from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^api/', include('content_gfk.api.urls')),
)
