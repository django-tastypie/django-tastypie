import time

from django.core.cache import cache
from django.test import TestCase
from django.utils.encoding import force_text

from tastypie.models import ApiAccess
from tastypie.throttle import BaseThrottle, CacheThrottle, CacheDBThrottle


class NoThrottleTestCase(TestCase):
    def test_init(self):
        throttle_1 = BaseThrottle()
        self.assertEqual(throttle_1.throttle_at, 150)
        self.assertEqual(throttle_1.timeframe, 3600)
        self.assertEqual(throttle_1.expiration, 604800)

        throttle_2 = BaseThrottle(throttle_at=50, timeframe=60*30, expiration=1)
        self.assertEqual(throttle_2.throttle_at, 50)
        self.assertEqual(throttle_2.timeframe, 1800)
        self.assertEqual(throttle_2.expiration, 1)

    def test_convert_identifier_to_key(self):
        throttle_1 = BaseThrottle()
        self.assertEqual(throttle_1.convert_identifier_to_key(''), '_accesses')
        self.assertEqual(throttle_1.convert_identifier_to_key('alnum10'), 'alnum10_accesses')
        self.assertEqual(throttle_1.convert_identifier_to_key('Mr. Pants'), 'Mr.Pants_accesses')
        self.assertEqual(throttle_1.convert_identifier_to_key('Mr_Pants'), 'Mr_Pants_accesses')
        self.assertEqual(throttle_1.convert_identifier_to_key('%^@@$&!a'), 'a_accesses')

    def test_should_be_throttled(self):
        throttle_1 = BaseThrottle()
        self.assertEqual(throttle_1.should_be_throttled('foobaz'), False)

    def test_accessed(self):
        throttle_1 = BaseThrottle()
        self.assertEqual(throttle_1.accessed('foobaz'), None)


class CacheThrottleTestCase(TestCase):
    def tearDown(self):
        cache.delete('daniel_accesses')
        cache.delete('cody_accesses')

    def test_throttling(self):
        throttle_1 = CacheThrottle(throttle_at=2, timeframe=5, expiration=2)

        self.assertEqual(throttle_1.should_be_throttled('daniel'), False)
        self.assertEqual(len(cache.get('daniel_accesses')), 0)
        self.assertEqual(throttle_1.accessed('daniel'), None)

        self.assertEqual(throttle_1.should_be_throttled('daniel'), False)
        self.assertEqual(len(cache.get('daniel_accesses')), 1)
        self.assertEqual(cache.get('cody_accesses'), None)
        self.assertEqual(throttle_1.accessed('daniel'), None)

        self.assertEqual(throttle_1.accessed('cody'), None)
        self.assertEqual(throttle_1.should_be_throttled('cody'), False)
        self.assertEqual(len(cache.get('daniel_accesses')), 2)
        self.assertEqual(len(cache.get('cody_accesses')), 1)

        # THROTTLE'D!
        self.assertEqual(throttle_1.should_be_throttled('daniel'), True)
        self.assertEqual(len(cache.get('daniel_accesses')), 2)
        self.assertEqual(throttle_1.accessed('daniel'), None)

        self.assertEqual(throttle_1.should_be_throttled('daniel'), True)
        self.assertEqual(len(cache.get('daniel_accesses')), 3)
        self.assertEqual(throttle_1.accessed('daniel'), None)

        # Should be no interplay.
        self.assertEqual(throttle_1.should_be_throttled('cody'), False)
        self.assertEqual(throttle_1.accessed('cody'), None)

        # Test the timeframe.
        time.sleep(3)
        self.assertEqual(throttle_1.should_be_throttled('daniel'), False)
        self.assertEqual(len(cache.get('daniel_accesses')), 0)


class CacheDBThrottleTestCase(TestCase):
    def tearDown(self):
        cache.delete('daniel_accesses')
        cache.delete('cody_accesses')

    def test_throttling(self):
        throttle_1 = CacheDBThrottle(throttle_at=2, timeframe=5, expiration=2)

        self.assertEqual(throttle_1.should_be_throttled('daniel'), False)
        self.assertEqual(len(cache.get('daniel_accesses')), 0)
        self.assertEqual(ApiAccess.objects.count(), 0)
        self.assertEqual(ApiAccess.objects.filter(identifier='daniel').count(), 0)
        self.assertEqual(throttle_1.accessed('daniel'), None)

        self.assertEqual(throttle_1.should_be_throttled('daniel'), False)
        self.assertEqual(len(cache.get('daniel_accesses')), 1)
        self.assertEqual(cache.get('cody_accesses'), None)
        self.assertEqual(ApiAccess.objects.count(), 1)
        self.assertEqual(ApiAccess.objects.filter(identifier='daniel').count(), 1)
        self.assertEqual(throttle_1.accessed('daniel'), None)

        self.assertEqual(throttle_1.accessed('cody'), None)
        self.assertEqual(throttle_1.should_be_throttled('cody'), False)
        self.assertEqual(len(cache.get('daniel_accesses')), 2)
        self.assertEqual(len(cache.get('cody_accesses')), 1)
        self.assertEqual(ApiAccess.objects.count(), 3)
        self.assertEqual(ApiAccess.objects.filter(identifier='daniel').count(), 2)
        self.assertEqual(throttle_1.accessed('cody'), None)

        # THROTTLE'D!
        self.assertEqual(throttle_1.accessed('daniel'), None)
        self.assertEqual(throttle_1.should_be_throttled('daniel'), True)
        self.assertEqual(len(cache.get('daniel_accesses')), 3)
        self.assertEqual(ApiAccess.objects.count(), 5)
        self.assertEqual(ApiAccess.objects.filter(identifier='daniel').count(), 3)

        self.assertEqual(throttle_1.accessed('daniel'), None)
        self.assertEqual(throttle_1.should_be_throttled('daniel'), True)
        self.assertEqual(len(cache.get('daniel_accesses')), 4)
        self.assertEqual(ApiAccess.objects.count(), 6)
        self.assertEqual(ApiAccess.objects.filter(identifier='daniel').count(), 4)

        # Should be no interplay.
        self.assertEqual(throttle_1.should_be_throttled('cody'), True)
        self.assertEqual(throttle_1.accessed('cody'), None)
        self.assertEqual(ApiAccess.objects.count(), 7)
        self.assertEqual(ApiAccess.objects.filter(identifier='daniel').count(), 4)

        # Test the timeframe.
        time.sleep(3)
        self.assertEqual(throttle_1.should_be_throttled('daniel'), False)
        self.assertEqual(len(cache.get('daniel_accesses')), 0)
        self.assertEqual(ApiAccess.objects.count(), 7)
        self.assertEqual(ApiAccess.objects.filter(identifier='daniel').count(), 4)


class ModelTestCase(TestCase):
    def test_unicode(self):
        access = ApiAccess(identifier="testing", accessed=0)
        self.assertEqual(force_text(access), 'testing @ 0')

