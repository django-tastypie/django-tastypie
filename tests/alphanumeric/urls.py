from django.conf.urls import patterns, include


urlpatterns = patterns('',
    (r'^api/', include('alphanumeric.api.urls')),
)
