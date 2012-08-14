from django.conf.urls.defaults import *

from api import api_router

urlpatterns = patterns('',
    (r'^api/(?P<rest>.*)', api_router.as_view()),
)
