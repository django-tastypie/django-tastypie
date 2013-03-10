from django.test import TestCase

from tastypie.test import ResourceTestCase


class TestApiClientTest(TestCase):
    def test_assertHttpAccepted(self):
        message = 'status_code is %s'
        if self.longMessage:  # in python2.7 longMessage is False
            message = 'False is not True : ' + message

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
            (message % Response.status_code,),
            cm.exception.args)
