from django.conf import settings
from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import User
from tastypie.api import Api
from django.contrib.auth.backends import ModelBackend
from core.models import Note
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource


class NoteAuthorBackend(ModelBackend):
    """
    NoteAuthorBackend is a Django authentication backend that answers True on
    all has_perm requests on Notes of which the user is the author.
    """
    supports_object_permissions = True
    supports_anonymous_user = False
    supports_anonymous_user_inactive_user = False

    def has_perm(self, user_obj, perm, obj=None):
        # Only check extra permissions for specific note instances
        if (obj is None or not isinstance(obj, Note)):
            return False

        # Finally, give add/modify/delete permissions to the author of the
        # article
        return obj.author == user_obj


class DjangoNoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)
        authorization = DjangoAuthorization()


class ObjectPermissionTestCase(TestCase):
    fixtures = ['note_testdata']

    def setUp(self):
        settings.AUTHENTICATION_BACKENDS = ('core.tests.NoteAuthorBackend',)
        api = Api()
        api.register(DjangoNoteResource())

    def test_delete_allowed_for_own_notes(self):
        request = HttpRequest()
        request.user = User.objects.get(username='johndoe')
        note1 = Note.objects.get(pk=1)
        note2 = Note.objects.get(pk=2)
        for method in ('GET', 'POST', 'PUT', 'DELETE'):
            request.method = method
            self.assertTrue(DjangoNoteResource()._meta.authorization.is_authorized(request, note1))
            self.assertTrue(DjangoNoteResource()._meta.authorization.is_authorized(request, note2))

    def test_delete_denied_for_others_notes(self):
        request = HttpRequest()
        request.user = User.objects.get(username='johndoe')
        note3 = Note.objects.get(pk=3)  # Jane's note
        for method in ('POST', 'PUT', 'DELETE'):  # 'GET' is free for anyone
            request.method = method
            self.assertFalse(DjangoNoteResource()._meta.authorization.is_authorized(request, note3))

