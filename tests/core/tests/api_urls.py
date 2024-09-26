from django.urls.conf import include, re_path

from core.tests.api import Api, NoteResource, UserResource

from tests.core.tests.api import SlowNoteResource

api = Api()
api.register(NoteResource())
api.register(UserResource())
api.register(SlowNoteResource())

urlpatterns = [
    re_path(r'^api/', include(api.urls)),
]
