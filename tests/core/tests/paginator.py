from django.test import TestCase
from tastypie.exceptions import BadRequest
from tastypie.paginator import Paginator
from core.models import Note
from core.tests.resources import NoteResource


class PaginatorTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def setUp(self):
        self.data_set = Note.objects.all()

    def test_page1(self):
        paginator = Paginator({}, self.data_set, resource_uri='/api/v1/notes/', limit=2, offset=0)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 0)
        self.assertEqual(meta['previous'], None)
        self.assertEqual(meta['next'], '/api/v1/notes/?limit=2&offset=2')
        self.assertEqual(meta['total_count'], 6)

    def test_page2(self):
        paginator = Paginator({}, self.data_set, resource_uri='/api/v1/notes/', limit=2, offset=2)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 2)
        self.assertEqual(meta['previous'], '/api/v1/notes/?limit=2&offset=0')
        self.assertEqual(meta['next'], '/api/v1/notes/?limit=2&offset=4')
        self.assertEqual(meta['total_count'], 6)

    def test_page3(self):
        paginator = Paginator({}, self.data_set, resource_uri='/api/v1/notes/', limit=2, offset=4)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 4)
        self.assertEqual(meta['previous'], '/api/v1/notes/?limit=2&offset=2')
        self.assertEqual(meta['next'], None)
        self.assertEqual(meta['total_count'], 6)

    def test_large_limit(self):
        paginator = Paginator({}, self.data_set, resource_uri='/api/v1/notes/', limit=20, offset=0)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 20)
        self.assertEqual(meta['offset'], 0)
        self.assertEqual(meta['previous'], None)
        self.assertEqual(meta['next'], None)
        self.assertEqual(meta['total_count'], 6)

    def test_limit(self):
        paginator = Paginator({}, self.data_set, limit=20, offset=0)

        paginator.limit = '10'
        self.assertEqual(paginator.get_limit(), 10)

        paginator.limit = None
        self.assertEqual(paginator.get_limit(), 20)

        paginator.limit = 10
        self.assertEqual(paginator.get_limit(), 10)

        paginator.limit = -10
        self.assertRaises(BadRequest, paginator.get_limit)

        paginator.limit = 'hAI!'
        self.assertRaises(BadRequest, paginator.get_limit)

    def test_offset(self):
        paginator = Paginator({}, self.data_set, limit=20, offset=0)

        paginator.offset = '10'
        self.assertEqual(paginator.get_offset(), 10)

        paginator.offset = 0
        self.assertEqual(paginator.get_offset(), 0)

        paginator.offset = 10
        self.assertEqual(paginator.get_offset(), 10)

        paginator.offset= -10
        self.assertRaises(BadRequest, paginator.get_offset)

        paginator.offset = 'hAI!'
        self.assertRaises(BadRequest, paginator.get_offset)
