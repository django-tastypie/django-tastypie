import base64
import python_digest
from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpRequest
from django.test import TestCase
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication, DigestAuthentication
from tastypie.http import HttpUnauthorized
from tastypie.models import ApiKey, create_api_key


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


class ApiKeyAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_is_authenticated(self):
        auth = ApiKeyAuthentication()
        request = HttpRequest()
        
        # Simulate sending the signal.
        john_doe = User.objects.get(username='johndoe')
        create_api_key(User, instance=john_doe, created=True)
        
        # No username/api_key details should fail.
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)
        
        # Wrong username details.
        request.GET['username'] = 'foo'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)
        
        # No api_key.
        request.GET['username'] = 'daniel'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)
        
        # Wrong user/api_key.
        request.GET['username'] = 'daniel'
        request.GET['api_key'] = 'foo'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)
        
        # Correct user/api_key.
        john_doe = User.objects.get(username='johndoe')
        request.GET['username'] = 'johndoe'
        request.GET['api_key'] = john_doe.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)

class DigestAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_is_authenticated(self):
        auth = DigestAuthentication()
        request = HttpRequest()
        
        # No HTTP Basic auth details should fail.
        auth_request = auth.is_authenticated(request)
        self.assertEqual(isinstance(auth_request, HttpUnauthorized), True)
        
        # HttpUnauthorized with auth type and realm
        self.assertEqual(auth_request['WWW-Authenticate'].find('Digest'), 0)
        self.assertEqual(auth_request['WWW-Authenticate'].find(' realm="django-tastypie"') > 0, True)
        self.assertEqual(auth_request['WWW-Authenticate'].find(' opaque=') > 0, True)
        self.assertEqual(auth_request['WWW-Authenticate'].find('nonce=') > 0, True)
        
        # Wrong basic auth details.
        request.META['HTTP_AUTHORIZATION'] = 'abcdefg'
        auth_request = auth.is_authenticated(request)
        self.assertEqual(isinstance(auth_request, HttpUnauthorized), True)
        
        # No password.
        request.META['HTTP_AUTHORIZATION'] = base64.b64encode('daniel')
        auth_request = auth.is_authenticated(request)
        self.assertEqual(isinstance(auth_request, HttpUnauthorized), True)
        
        # Wrong user/password.
        request.META['HTTP_AUTHORIZATION'] = base64.b64encode('daniel:pass')
        auth_request = auth.is_authenticated(request)
        self.assertEqual(isinstance(auth_request, HttpUnauthorized), True)
        
        # Correct user/password.
        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = python_digest.build_authorization_request(
            john_doe.username,
            request.method,
            '/', # uri
            1,   # nonce_count
            digest_challenge=auth_request['WWW-Authenticate'],
            password=john_doe.api_key.key)
        auth_request = auth.is_authenticated(request)
        self.assertEqual(auth_request, True)
