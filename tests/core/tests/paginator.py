# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase
from tastypie.exceptions import BadRequest
from tastypie.paginator import Paginator
from core.models import Note
from core.tests.resources import NoteResource
from django.db import reset_queries


class PaginatorTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def setUp(self):
        super(PaginatorTestCase, self).setUp()
        self.data_set = Note.objects.all()
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
    
    def tearDown(self):
        settings.DEBUG = self.old_debug
        super(PaginatorTestCase, self).tearDown()
    
    def _get_query_count(self):
        try:
            from django.db import connections
            return connections['default'].queries
        except ImportError:
            from django.db import connection
            return connection.queries

    def test_page1(self):
        reset_queries()
        self.assertEqual(len(self._get_query_count()), 0)
        
        paginator = Paginator({}, self.data_set, resource_uri='/api/v1/notes/', limit=2, offset=0)
        
        # REGRESSION: Check to make sure only part of the cache is full.
        # We used to run ``len()`` on the ``QuerySet``, which would populate
        # the entire result set. Owwie.
        paginator.get_count()
        self.assertEqual(len(self._get_query_count()), 1)
        # Should be nothing in the cache.
        self.assertEqual(paginator.objects._result_cache, None)
        
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
    
    def test_all(self):
        paginator = Paginator({'limit': 0}, self.data_set, resource_uri='/api/v1/notes/', limit=2, offset=0)
        page = paginator.page()
        meta = page['meta']
        self.assertEqual(meta['limit'], 0)
        self.assertEqual(meta['offset'], 0)
        self.assertEqual(meta['total_count'], 6)
        self.assertEqual(len(page['objects']), 6)
        self.assertFalse('previous' in meta)
        self.assertFalse('next' in meta)
    
    def test_complex_get(self):
        request = {
            'slug__startswith': 'food',
            'format': 'json',
        }
        paginator = Paginator(request, self.data_set, resource_uri='/api/v1/notes/', limit=2, offset=2)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 2)
        self.assertEqual(meta['previous'], '/api/v1/notes/?slug__startswith=food&offset=0&limit=2&format=json')
        self.assertEqual(meta['next'], '/api/v1/notes/?slug__startswith=food&offset=4&limit=2&format=json')
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
    
    def test_regression_nonqueryset(self):
        paginator = Paginator({}, ['foo', 'bar', 'baz'], limit=2, offset=0)
        # This would fail due to ``count`` being present on ``list`` but called
        # differently.
        page = paginator.page()
        self.assertEqual(page['objects'], ['foo', 'bar'])
    
    def test_unicode_request(self):
        request = {
            'slug__startswith': u'☃',
            'format': 'json',
        }
        paginator = Paginator(request, self.data_set, resource_uri='/api/v1/notes/', limit=2, offset=2)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 2)
        self.assertEqual(meta['previous'], '/api/v1/notes/?slug__startswith=%E2%98%83&offset=0&limit=2&format=json')
        self.assertEqual(meta['next'], u'/api/v1/notes/?slug__startswith=%E2%98%83&offset=4&limit=2&format=json')
        self.assertEqual(meta['total_count'], 6)
