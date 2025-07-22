from django.urls import include, re_path as url


urlpatterns = [
    url(r'^api/', include('content_gfk.api.urls')),
]
