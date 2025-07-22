from django.urls import include, re_path as url


urlpatterns = [
    url(r'^api/', include('gis.api.urls')),
]
