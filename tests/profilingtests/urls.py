try:
    from django.conf.urls import patterns, include
except ImportError:  # Django < 1.4
    from django.conf.urls.defaults import patterns, include

from tastypie.api import Api

from .resources import NoteResource, UserResource


api = Api()
api.register(NoteResource())
api.register(UserResource())

urlpatterns = patterns('',
    (r'^api/', include(api.urls)),
)
