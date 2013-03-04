try:
    from django.conf.urls import *
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import *
from core.tests.api import Api, NoteResource, UserResource


api = Api()
api.register(NoteResource())
api.register(UserResource())

urlpatterns = patterns('',
    (r'^api/', include(api.urls)),
)
