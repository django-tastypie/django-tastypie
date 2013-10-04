from django.test import TestCase
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from tastypie.contrib.contenttypes.resources import GenericResource

from content_gfk.models import Note, Definition
from content_gfk.api.resources import NoteResource, DefinitionResource


class GenericResourceTestCase(TestCase):
    def setUp(self):
        self.resource = GenericResource({Note: NoteResource,
                                         Definition: DefinitionResource})

    def test_bad_uri(self):
        bad_uri = '/bad_uri/'
        self.assertRaises(NotFound, self.resource.get_via_uri, bad_uri)

    def test_resource_not_registered(self):
        bad_uri = '/api/v1/quotes/1/'
        self.assertRaises(NotFound, self.resource.get_via_uri, bad_uri)

    def test_hydrate(self):
        data = {'content_type': 'note',
                'title': 'All aboard the rest train',
                'content': 'Sometimes it is just better to lorem ipsum'}
        bundle = self.resource.full_hydrate(Bundle(data=data))
        self.assertTrue(isinstance(bundle.obj, Note))
        self.assertEqual(bundle.obj.title, data['title'])
        self.assertEqual(bundle.obj.content, data['content'])

    def test_dehydrate(self):
        note_1 = Note.objects.create(
            title='All aboard the rest train',
            content='Sometimes it is just better to lorem ipsum'
        )
        bundle = self.resource.full_dehydrate(Bundle(obj=note_1))
        self.assertEqual(bundle.data['content_type'], 'note')
        self.assertEqual(bundle.data['title'], note_1.title)
        self.assertEqual(bundle.data['content'], note_1.content)

