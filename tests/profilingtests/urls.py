from django.conf.urls import include, url

from tastypie.api import Api

from .resources import NoteResource, UserResource


api = Api()
api.register(NoteResource())
api.register(UserResource())

urlpatterns = [
    url(r'^api/', include(api.urls)),
]
