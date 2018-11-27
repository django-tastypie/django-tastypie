from django.conf.urls import include, url

from core.tests.api import Api, NoteResource, UserResource


api = Api()
api.register(NoteResource())
api.register(UserResource())

urlpatterns = [
    url(r'^api/', include(api.urls)),
]
