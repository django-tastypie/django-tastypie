from django.urls.conf import include, re_path


urlpatterns = [
    re_path(r'^api/', include('gis.api.urls')),
]
