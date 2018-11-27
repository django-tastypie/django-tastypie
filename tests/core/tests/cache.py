import mock

from django.core.cache import cache
from django.test import TestCase

from tastypie.cache import NoCache, SimpleCache


class NoCacheTestCase(TestCase):
    def tearDown(self):
        cache.delete('foo')
        cache.delete('moof')
        super(NoCacheTestCase, self).tearDown()

    def test_get(self):
        cache.set('foo', 'bar', 60)
        cache.set('moof', 'baz', 1)

        no_cache = NoCache()
        self.assertEqual(no_cache.get('foo'), None)
        self.assertEqual(no_cache.get('moof'), None)
        self.assertEqual(no_cache.get(''), None)

    def test_set(self):
        no_cache = NoCache()
        no_cache.set('foo', 'bar')
        no_cache.set('moof', 'baz', timeout=1)

        # Use the underlying cache system to verify.
        self.assertEqual(cache.get('foo'), None)
        self.assertEqual(cache.get('moof'), None)


class SimpleCacheTestCase(TestCase):
    def tearDown(self):
        cache.delete('foo')
        cache.delete('moof')
        super(SimpleCacheTestCase, self).tearDown()

    def test_get(self):
        cache.set('foo', 'bar', 60)
        cache.set('moof', 'baz', 1)

        simple_cache = SimpleCache()
        self.assertEqual(simple_cache.get('foo'), 'bar')
        self.assertEqual(simple_cache.get('moof'), 'baz')
        self.assertEqual(simple_cache.get(''), None)

    def test_set(self):
        simple_cache = SimpleCache(timeout=1)

        with mock.patch.object(simple_cache, 'cache', mock.Mock(wraps=simple_cache.cache)) as mocked_cache:
            simple_cache.set('foo', 'bar', timeout=10)
            simple_cache.set('moof', 'baz')

        # Use the underlying cache system to verify.
        self.assertEqual(cache.get('foo'), 'bar')
        self.assertEqual(cache.get('moof'), 'baz')

        # make sure cache was called with correct timeouts.
        self.assertEqual(mocked_cache.set.call_args_list[0][0][2], 10)
        self.assertEqual(mocked_cache.set.call_args_list[1][0][2], 1)
