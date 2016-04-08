# Basically just a sanity check to make sure things don't change from underneath us.
from django.test import TestCase

from tastypie import http


class HttpTestCase(TestCase):
    def test_201(self):
        response = http.HttpCreated(location='http://example.com/thingy/1/')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['Location'], 'http://example.com/thingy/1/')

    def test_201_no_location(self):
        # Regression.
        response = http.HttpCreated()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['Location'], '')

    def test_202(self):
        response = http.HttpAccepted()
        self.assertEqual(response.status_code, 202)

    def test_204(self):
        response = http.HttpNoContent()
        self.assertEqual(response.status_code, 204)

    def test_303(self):
        response = http.HttpSeeOther()
        self.assertEqual(response.status_code, 303)

    def test_304(self):
        response = http.HttpNotModified()
        self.assertEqual(response.status_code, 304)

    def test_400(self):
        response = http.HttpBadRequest()
        self.assertEqual(response.status_code, 400)

    def test_401(self):
        response = http.HttpUnauthorized()
        self.assertEqual(response.status_code, 401)

    def test_404(self):
        response = http.HttpNotFound()
        self.assertEqual(response.status_code, 404)

    def test_405(self):
        response = http.HttpMethodNotAllowed()
        self.assertEqual(response.status_code, 405)

    def test_406(self):
        response = http.HttpNotAcceptable()
        self.assertEqual(response.status_code, 406)

    def test_409(self):
        response = http.HttpConflict()
        self.assertEqual(response.status_code, 409)

    def test_410(self):
        response = http.HttpGone()
        self.assertEqual(response.status_code, 410)

    def test_415(self):
        response = http.HttpUnsupportedMediaType()
        self.assertEqual(response.status_code, 415)

    def test_429(self):
        response = http.HttpTooManyRequests()
        self.assertEqual(response.status_code, 429)

    def test_501(self):
        response = http.HttpNotImplemented()
        self.assertEqual(response.status_code, 501)
