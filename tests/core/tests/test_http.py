# Basically just a sanity check to make sure things don't change from underneath us.
from django.test import TestCase
from tastypie.http import *


class HttpTestCase(TestCase):
    def test_various_statuses(self):
        created = HttpCreated(location='http://example.com/thingy/1/')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created['Location'], 'http://example.com/thingy/1/')
        # Regression.
        created_2 = HttpCreated()
        self.assertEqual(created_2.status_code, 201)
        self.assertEqual(created_2['Location'], '')
        accepted = HttpAccepted()
        self.assertEqual(accepted.status_code, 202)
        no_content = HttpNoContent()
        self.assertEqual(no_content.status_code, 204)
        see_other = HttpSeeOther()
        self.assertEqual(see_other.status_code, 303)
        not_modified = HttpNotModified()
        self.assertEqual(not_modified.status_code, 304)
        bad_request = HttpBadRequest()
        self.assertEqual(bad_request.status_code, 400)
        unauthorized = HttpUnauthorized()
        self.assertEqual(unauthorized.status_code, 401)
        not_found = HttpNotFound()
        self.assertEqual(not_found.status_code, 404)
        not_allowed = HttpMethodNotAllowed()
        self.assertEqual(not_allowed.status_code, 405)
        conflict = HttpConflict()
        self.assertEqual(conflict.status_code, 409)
        gone = HttpGone()
        self.assertEqual(gone.status_code, 410)
        toomanyrequests = HttpTooManyRequests()
        self.assertEqual(toomanyrequests.status_code, 429)
        not_implemented = HttpNotImplemented()
        self.assertEqual(not_implemented.status_code, 501)
