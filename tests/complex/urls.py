try:
    from django.conf.urls import *
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^api/', include('complex.api.urls')),
)
