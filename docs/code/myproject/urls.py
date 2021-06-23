from django.urls import include, re_path
from django.contrib import admin

urlpatterns = [
    # Examples:
    # re_path(r'^$', 'myproject.views.home', name='home'),
    # re_path(r'^blog/', include('blog.urls')),

    re_path(r'^admin/', include(admin.site.urls)),
]
