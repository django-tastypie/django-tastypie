from django.urls.conf import include, re_path
from django.contrib import admin

urlpatterns = [
    # Examples:
    # url(r'^$', 'myproject.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    re_path(r'^admin/', include(admin.site.urls)),
]
