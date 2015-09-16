from django.conf.urls import patterns, include


urlpatterns = patterns('',
    (r'^api/', include('content_gfk.api.urls')),
)
