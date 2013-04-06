try:
    from django.conf.urls import patterns, include
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import patterns, include

urlpatterns = patterns('',
    (r'^api/', include('basic.api.urls')),
)
