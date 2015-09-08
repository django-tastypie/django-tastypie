from django.conf.urls import patterns, include


urlpatterns = patterns('',
    (r'^api/', include('basic.api.urls')),
)
