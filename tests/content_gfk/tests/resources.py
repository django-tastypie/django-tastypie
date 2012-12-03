from django.test import TestCase
from tastypie.exceptions import NotFound
from tastypie.contrib.contenttypes.resources import GenericResource

from core.tests.mocks import MockRequest
from content_gfk.api.resources import NoteResource, DefinitionResource
from content_gfk.models import Note


class GenericResourceTestCase(TestCase):
    def setUp(self):
        self.resource = GenericResource([NoteResource, DefinitionResource])

    def test_bad_uri(self):
        bad_uri = '/bad_uri/'
        self.assertRaises(NotFound, self.resource.get_via_uri, bad_uri)

    def test_resource_not_registered(self):
        bad_uri = '/api/v1/quotes/1/'
        self.assertRaises(NotFound, self.resource.get_via_uri, bad_uri)

    def test_resource_passes_request(self):
        note = Note.objects.create(
            title='All aboard the rest train',
            content='Sometimes it is just better to lorem ipsum'
        )

        uri = '/api/v1/notes/1/'

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        result = self.resource.get_via_uri(uri, request=request)
        self.assertEqual(result, note)
