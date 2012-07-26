import time
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
        self.assertRaises(NotImplementedError,no_cache.get,'foo')
        self.assertRaises(NotImplementedError,no_cache.get,'moof')
        self.assertRaises(NotImplementedError,no_cache.get,'')

    def test_set(self):
        no_cache = NoCache()
        self.assertRaises(NotImplementedError,no_cache.set,'foo', 'bar')
        self.assertRaises(NotImplementedError,no_cache.set,'moof', 'baz', timeout=1)
        
        # Use the underlying cache system to verify.
        self.assertEqual(cache.get('foo'), None)
        self.assertEqual(cache.get('moof'), None)

    def test_delete(self):
        cache.set('foo', 'bar', 60)
        cache.set('moof', 'baz', 1)

        no_cache = NoCache()
        self.assertRaises(NotImplementedError,no_cache.delete,'foo')
        self.assertRaises(NotImplementedError,no_cache.delete,'moof')

        # The test_delete will not actually delete the data in the underlying cache system.
        self.assertEqual(cache.get('foo'), 'bar')
        self.assertEqual(cache.get('moof'), 'baz')        

    def test_delete_many(self):
        cache.set('foo', 'bar', 60)
        cache.set('moof', 'baz', 1)

        no_cache = NoCache()
        self.assertRaises(NotImplementedError,no_cache.delete_many,['foo','moof'])

        # The test_delete_many will not actually delete the data in the underlying cache system.
        self.assertEqual(cache.get('foo'), 'bar')
        self.assertEqual(cache.get('moof'), 'baz')      


class OptionalMethodsTestCase(TestCase):
    def tearDown(self):
        cache.delete('foo')
        cache.delete('moof')
        super(OptionalMethodsTestCase, self).tearDown()

    def test_delete_many(self):
        cache.set('foo', 'bar', 60)
        cache.set('moof', 'baz', 1)
        
        class DeleteManyTestCache(NoCache):
            def delete(self, key):
                cache.delete(key)
        
        optional_cache =  DeleteManyTestCache()
        optional_cache.delete_many(['foo','moof'])
        
        # Should fail-over to ``delete`` method, i.e., loop through all the key in keys
        # and delete the data in the underlying cache system.
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
        simple_cache.set('foo', 'bar', timeout=10)
        simple_cache.set('moof', 'baz')

        # Use the underlying cache system to verify.
        self.assertEqual(cache.get('foo'), 'bar')
        self.assertEqual(cache.get('moof'), 'baz')

        # Check expiration.
        time.sleep(2)
        self.assertEqual(cache.get('moof'), None)
        self.assertEqual(cache.get('foo'), 'bar')

    def test_delete(self):
        simple_cache = SimpleCache()
        simple_cache.set('foo', 'bar')
        simple_cache.set('moof', 'baz')
        
        simple_cache.delete('foo')
        
        # Use the underlying cache system to verify.
        self.assertEqual(cache.get('foo'), None)
        self.assertEqual(cache.get('moof'), 'baz')        

    def test_delete_many(self):
        simple_cache = SimpleCache()
        simple_cache.set('foo', 'bar')
        simple_cache.set('moof', 'baz')
        
        simple_cache.delete_many(['foo','moof'])
        
        # Use the underlying cache system to verify.
        self.assertEqual(cache.get('foo'), None)
        self.assertEqual(cache.get('moof'), None)        
        
