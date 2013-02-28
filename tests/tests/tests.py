from django.test import TestCase

from tastypie.test import ResourceTestCase


class TestApiClientTest(TestCase):
    def test_assertHttpAccepted(self):
        class SomeTest(ResourceTestCase):
            def runTest(self):
                pass

        class Response(object):
            status_code = 405

        tc = SomeTest()
        response = Response()

        with self.assertRaises(AssertionError) as cm:
            tc.assertHttpAccepted(response)

        self.assertEqual(
            ('False is not True : status_code is %s' % Response.status_code,),
            cm.exception.args)
