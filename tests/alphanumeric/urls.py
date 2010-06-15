from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^api/', include('alphanumeric.api.urls')),
)
