from django.urls import include, re_path as url


urlpatterns = [
    url(r'^api/', include('alphanumeric.api.urls')),
]
