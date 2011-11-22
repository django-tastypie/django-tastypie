from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^api/', include('biginteger.api.urls')),
)
