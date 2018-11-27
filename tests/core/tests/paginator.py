# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import connections, reset_queries
from django.http import QueryDict
from django.test import TestCase

from tastypie.exceptions import BadRequest
from tastypie.paginator import Paginator

from core.models import Note


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
        return connections['default'].queries

    def test_page1(self):
        reset_queries()
        self.assertEqual(len(self._get_query_count()), 0)

        paginator = Paginator({}, self.data_set,
            resource_uri='/api/v1/notes/', limit=2, offset=0)

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
        self.assertTrue('limit=2' in meta['next'])
        self.assertTrue('offset=2' in meta['next'])
        self.assertEqual(meta['total_count'], 6)

    def test_page2(self):
        paginator = Paginator({}, self.data_set,
            resource_uri='/api/v1/notes/', limit=2, offset=2)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 2)
        self.assertTrue('limit=2' in meta['previous'])
        self.assertTrue('offset=0' in meta['previous'])
        self.assertTrue('limit=2' in meta['next'])
        self.assertTrue('offset=4' in meta['next'])
        self.assertEqual(meta['total_count'], 6)

    def test_page3(self):
        paginator = Paginator({}, self.data_set,
            resource_uri='/api/v1/notes/', limit=2, offset=4)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 4)
        self.assertTrue('limit=2' in meta['previous'])
        self.assertTrue('offset=2' in meta['previous'])
        self.assertEqual(meta['next'], None)
        self.assertEqual(meta['total_count'], 6)

    def test_page2_with_request(self):
        for req in [{'offset': '2', 'limit': '2'},
                QueryDict('offset=2&limit=2')]:
            paginator = Paginator(req, self.data_set,
                resource_uri='/api/v1/notes/', limit=2, offset=2)
            meta = paginator.page()['meta']
            self.assertEqual(meta['limit'], 2)
            self.assertEqual(meta['offset'], 2)
            self.assertTrue('limit=2' in meta['previous'])
            self.assertTrue('offset=0' in meta['previous'])
            self.assertTrue('limit=2' in meta['next'])
            self.assertTrue('offset=4' in meta['next'])
            self.assertEqual(meta['total_count'], 6)

    def test_page3_with_request(self):
        for req in [{'offset': '4', 'limit': '2'},
                QueryDict('offset=4&limit=2')]:
            paginator = Paginator(req, self.data_set,
                resource_uri='/api/v1/notes/', limit=2, offset=4)
            meta = paginator.page()['meta']
            self.assertEqual(meta['limit'], 2)
            self.assertEqual(meta['offset'], 4)
            self.assertTrue('limit=2' in meta['previous'])
            self.assertTrue('offset=2' in meta['previous'])
            self.assertEqual(meta['next'], None)
            self.assertEqual(meta['total_count'], 6)

    def test_large_limit(self):
        paginator = Paginator({}, self.data_set,
            resource_uri='/api/v1/notes/', limit=20, offset=0)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 20)
        self.assertEqual(meta['offset'], 0)
        self.assertEqual(meta['previous'], None)
        self.assertEqual(meta['next'], None)
        self.assertEqual(meta['total_count'], 6)

    def test_all(self):
        paginator = Paginator({'limit': 0}, self.data_set,
            resource_uri='/api/v1/notes/', limit=2, offset=0)
        page = paginator.page()
        meta = page['meta']
        self.assertEqual(meta['limit'], 1000)
        self.assertEqual(meta['offset'], 0)
        self.assertEqual(meta['total_count'], 6)
        self.assertEqual(len(page['objects']), 6)

    def test_complex_get(self):
        request = {
            'slug__startswith': 'food',
            'format': 'json',
        }
        paginator = Paginator(request, self.data_set,
            resource_uri='/api/v1/notes/', limit=2, offset=2)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 2)
        self.assertTrue('limit=2' in meta['previous'])
        self.assertTrue('offset=0' in meta['previous'])
        self.assertTrue('slug__startswith=food' in meta['previous'])
        self.assertTrue('format=json' in meta['previous'])
        self.assertTrue('limit=2' in meta['next'])
        self.assertTrue('offset=4' in meta['next'])
        self.assertTrue('slug__startswith=food' in meta['next'])
        self.assertTrue('format=json' in meta['next'])
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
        raised = False
        try:
            paginator.get_limit()
        except BadRequest as e:
            raised = e
        self.assertTrue(raised)
        self.assertEqual(str(raised), "Invalid limit '-10' provided. Please provide a positive integer >= 0.")

        paginator.limit = 'hAI!'
        raised = False
        try:
            paginator.get_limit()
        except BadRequest as e:
            raised = e
        self.assertTrue(raised)
        self.assertEqual(str(raised), "Invalid limit 'hAI!' provided. Please provide a positive integer.")

        # Test the max_limit.
        paginator.limit = 1000
        self.assertEqual(paginator.get_limit(), 1000)

        paginator.limit = 1001
        self.assertEqual(paginator.get_limit(), 1000)

        paginator = Paginator({},
            self.data_set, limit=20, offset=0, max_limit=10)
        self.assertEqual(paginator.get_limit(), 10)

    def test_offset(self):
        paginator = Paginator({}, self.data_set, limit=20, offset=0)

        paginator.offset = '10'
        self.assertEqual(paginator.get_offset(), 10)

        paginator.offset = 0
        self.assertEqual(paginator.get_offset(), 0)

        paginator.offset = 10
        self.assertEqual(paginator.get_offset(), 10)

        paginator.offset = -10
        raised = False
        try:
            paginator.get_offset()
        except BadRequest as e:
            raised = e
        self.assertTrue(raised)
        self.assertEqual(str(raised), "Invalid offset '-10' provided. Please provide a positive integer >= 0.")

        paginator.offset = 'hAI!'
        raised = False
        try:
            paginator.get_offset()
        except BadRequest as e:
            raised = e
        self.assertTrue(raised)
        self.assertEqual(str(raised), "Invalid offset 'hAI!' provided. Please provide an integer.")

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
        paginator = Paginator(request, self.data_set,
            resource_uri='/api/v1/notes/', limit=2, offset=2)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 2)
        self.assertTrue('limit=2' in meta['previous'])
        self.assertTrue('offset=0' in meta['previous'])
        self.assertTrue('slug__startswith=%E2%98%83' in meta['previous'])
        self.assertTrue('format=json' in meta['previous'])
        self.assertTrue('limit=2' in meta['next'])
        self.assertTrue('offset=4' in meta['next'])
        self.assertTrue('slug__startswith=%E2%98%83' in meta['next'])
        self.assertTrue('format=json' in meta['next'])
        self.assertEqual(meta['total_count'], 6)

        request = QueryDict('slug__startswith=☃&format=json')
        paginator = Paginator(request, self.data_set,
            resource_uri='/api/v1/notes/', limit=2, offset=2)
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 2)
        self.assertTrue('limit=2' in meta['previous'])
        self.assertTrue('offset=0' in meta['previous'])
        self.assertTrue('slug__startswith=%E2%98%83' in meta['previous'])
        self.assertTrue('format=json' in meta['previous'])
        self.assertTrue('limit=2' in meta['next'])
        self.assertTrue('offset=4' in meta['next'])
        self.assertTrue('slug__startswith=%E2%98%83' in meta['next'])
        self.assertTrue('format=json' in meta['next'])
        self.assertEqual(meta['total_count'], 6)

    def test_custom_collection_name(self):
        paginator = Paginator({}, self.data_set,
            resource_uri='/api/v1/notes/', limit=20, offset=0,
            collection_name='notes')
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 20)
        self.assertEqual(meta['offset'], 0)
        self.assertEqual(meta['previous'], None)
        self.assertEqual(meta['next'], None)
        self.assertEqual(meta['total_count'], 6)
        self.assertEqual(len(paginator.page()['notes']), 6)

    def test_multiple(self):
        request = QueryDict('a=1&a=2')
        paginator = Paginator(request, self.data_set,
            resource_uri='/api/v1/notes/', limit='2', offset='2')
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 2)
        self.assertEqual(meta['offset'], 2)
        self.assertTrue('limit=2' in meta['previous'])
        self.assertTrue('offset=0' in meta['previous'])
        self.assertTrue('a=1' in meta['previous'])
        self.assertTrue('a=2' in meta['previous'])
        self.assertTrue('limit=2' in meta['next'])
        self.assertTrue('offset=4' in meta['next'])
        self.assertTrue('a=1' in meta['next'])
        self.assertTrue('a=2' in meta['next'])

    def test_max_limit(self):
        paginator = Paginator({'limit': 0}, self.data_set, max_limit=10,
            resource_uri='/api/v1/notes/')
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 10)

    def test_max_limit_none(self):
        paginator = Paginator({'limit': 0}, self.data_set, max_limit=None,
            resource_uri='/api/v1/notes/')
        meta = paginator.page()['meta']
        self.assertEqual(meta['limit'], 0)
