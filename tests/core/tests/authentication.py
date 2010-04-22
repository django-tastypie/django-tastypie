import base64
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
from tastypie.authentication import Authentication, BasicAuthentication
from tastypie.http import HttpUnauthorized

class AuthenticationTestCase(TestCase):
    def test_is_authenticated(self):
        auth = Authentication()
        request = HttpRequest()
        # Doesn't matter. Always true.
        self.assertTrue(auth.is_authenticated(None))
        self.assertTrue(auth.is_authenticated(request))
    
    def test_get_identifier(self):
        auth = Authentication()
        request = HttpRequest()
        self.assertEqual(auth.get_identifier(request), 'noaddr_nohost')
        
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['REMOTE_HOST'] = 'nebula.local'
        self.assertEqual(auth.get_identifier(request), '127.0.0.1_nebula.local')


class BasicAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_is_authenticated(self):
        auth = BasicAuthentication()
        request = HttpRequest()
        
        # No HTTP Basic auth details should fail.
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # HttpUnauthorized with auth type and realm
        self.assertEqual(auth.is_authenticated(request)['WWW-Authenticate'], 'Basic Realm="django-tastypie"')
        
        # Wrong basic auth details.
        request.META['HTTP_AUTHORIZATION'] = 'abcdefg'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)
        
        # No password.
        request.META['HTTP_AUTHORIZATION'] = base64.b64encode('daniel')
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)
        
        # Wrong user/password.
        request.META['HTTP_AUTHORIZATION'] = base64.b64encode('daniel:pass')
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)
        
        # Correct user/password.
        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('johndoe:pass')
        self.assertEqual(auth.is_authenticated(request), True)
