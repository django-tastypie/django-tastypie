from django.urls.conf import include, re_path

from core.tests.api import Api, NoteResource, UserResource


api = Api()
api.register(NoteResource())
api.register(UserResource())

urlpatterns = [
    re_path(r'^api/', include(api.urls)),
]
