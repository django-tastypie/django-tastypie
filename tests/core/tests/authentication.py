import base64
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
from tastypie.authentication import Authentication, BasicAuthentication


class AuthenticationTestCase(TestCase):
    def test_is_authorized(self):
        auth = Authentication()
        request = HttpRequest()
        # Doesn't matter. Always true.
        self.assertTrue(auth.is_authorized(None))
        self.assertTrue(auth.is_authorized(request))


class BasicAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_is_authorized(self):
        auth = BasicAuthentication()
        request = HttpRequest()
        
        # No HTTP Basic auth details should fail.
        self.assertEqual(auth.is_authorized(request), False)
        
        # Wrong basic auth details.
        request.META['HTTP_AUTHORIZATION'] = 'abcdefg'
        self.assertEqual(auth.is_authorized(request), False)
        
        # No password.
        request.META['HTTP_AUTHORIZATION'] = base64.b64encode('daniel')
        self.assertEqual(auth.is_authorized(request), False)
        
        # Wrong user/password.
        request.META['HTTP_AUTHORIZATION'] = base64.b64encode('daniel:pass')
        self.assertEqual(auth.is_authorized(request), False)
        
        # Correct user/password.
        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = base64.b64encode('johndoe:pass')
        self.assertEqual(auth.is_authorized(request), True)
