from django.test import TestCase
from tastypie.exceptions import NotFound
from tastypie.contrib.contenttypes.resources import GenericResource

from content_gfk.api.resources import NoteResource, DefinitionResource


class GenericResourceTestCase(TestCase):
    def setUp(self):
        self.resource = GenericResource([NoteResource, DefinitionResource])


    def test_bad_uri(self):
        bad_uri = '/bad_uri/'
        self.assertRaises(NotFound, self.resource.get_via_uri, bad_uri)


    def test_resource_not_registered(self):
        bad_uri = '/api/v1/quotes/1/'
        self.assertRaises(NotFound, self.resource.get_via_uri, bad_uri)
