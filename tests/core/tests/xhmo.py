"""
Tests that the X-HTTP-Method-Override header works.
"""

from django.http import HttpRequest
from django.test import TestCase
from core.tests.resources import NoteResource

class XHMOTests(TestCase):
    def test_method_check_respects_xhmo(self):
        """The X-HTTP-Method-Override header should override POST requests"""
        resource = NoteResource()
        request = HttpRequest()
        request.method = 'POST'
        request.META['HTTP_X_HTTP_METHOD_OVERRIDE'] = 'DELETE'
        method = resource.method_check(request, resource._meta.allowed_methods)
        self.assertEqual(method.lower(), 'delete')

    def test_method_check_ignores_hxmo_on_non_post_requests(self):
        """X-HTTP-Method-Override should only be respected on POSTs"""
        resource = NoteResource()
        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_X_HTTP_METHOD_OVERRIDE'] = 'DELETE'
        method = resource.method_check(request, resource._meta.allowed_methods)
        self.assertEqual(method.lower(), 'get')
