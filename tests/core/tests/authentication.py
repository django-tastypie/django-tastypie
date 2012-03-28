import base64
import time
import warnings
from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpRequest
from django.test import TestCase
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication, DigestAuthentication, OAuthAuthentication
from tastypie.http import HttpUnauthorized
from tastypie.models import ApiKey, create_api_key


# Be tricky.
from tastypie.authentication import python_digest, oauth2, oauth_provider
if python_digest is None:
    warnings.warn("Running tests without python_digest! Bad news!")
if oauth2 is None:
    warnings.warn("Running tests without oauth2! Bad news!")
if oauth_provider is None:
    warnings.warn("Running tests without oauth_provider! Bad news!")


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

        # Regression: Password with colon.
        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass:word')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('johndoe:pass:word')
        self.assertEqual(auth.is_authenticated(request), True)

        # Capitalization shouldn't matter.
        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass:word')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'bAsIc %s' % base64.b64encode('johndoe:pass:word')
        self.assertEqual(auth.is_authenticated(request), True)


class ApiKeyAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def setUp(self):
        super(ApiKeyAuthenticationTestCase, self).setUp()
        ApiKey.objects.all().delete()

    def test_is_authenticated_get_params(self):
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

    def test_is_authenticated_header(self):
        auth = ApiKeyAuthentication()
        request = HttpRequest()

        # Simulate sending the signal.
        john_doe = User.objects.get(username='johndoe')
        create_api_key(User, instance=john_doe, created=True)

        # No username/api_key details should fail.
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Wrong username details.
        request.META['HTTP_AUTHORIZATION'] = 'foo'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # No api_key.
        request.META['HTTP_AUTHORIZATION'] = 'ApiKey daniel'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Wrong user/api_key.
        request.META['HTTP_AUTHORIZATION'] = 'ApiKey daniel:pass'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Correct user/api_key.
        john_doe = User.objects.get(username='johndoe')
        request.META['HTTP_AUTHORIZATION'] = 'ApiKey johndoe:%s' % john_doe.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)

        # Capitalization shouldn't matter.
        john_doe = User.objects.get(username='johndoe')
        request.META['HTTP_AUTHORIZATION'] = 'aPiKeY johndoe:%s' % john_doe.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)


class DigestAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def setUp(self):
        super(DigestAuthenticationTestCase, self).setUp()
        ApiKey.objects.all().delete()

    def test_is_authenticated(self):
        auth = DigestAuthentication()
        request = HttpRequest()

        # Simulate sending the signal.
        john_doe = User.objects.get(username='johndoe')
        create_api_key(User, instance=john_doe, created=True)

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
        request.META['HTTP_AUTHORIZATION'] = python_digest.build_authorization_request(
            john_doe.username,
            request.method,
            '/', # uri
            1,   # nonce_count
            digest_challenge=auth_request['WWW-Authenticate'],
            password=john_doe.api_key.key
        )
        auth_request = auth.is_authenticated(request)
        self.assertEqual(auth_request, True)


class OAuthAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_is_authenticated(self):
        from oauth_provider.models import Consumer, Token, Resource
        auth = OAuthAuthentication()
        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testsuite'
        request.META['SERVER_PORT'] = '8080'
        request.REQUEST = request.GET = {}
        request.method = "GET"

        # Invalid request.
        resp = auth.is_authenticated(request)
        self.assertEqual(resp.status_code, 401)

        # No username/api_key details should fail.
        request.REQUEST = request.GET = {
            'oauth_consumer_key': '123',
            'oauth_nonce': 'abc',
            'oauth_signature': '&',
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': 'foo',
        }
        user = User.objects.create_user('daniel', 'test@example.com', 'password')
        request.META['Authorization'] = 'OAuth ' + ','.join([key+'='+value for key, value in request.REQUEST.items()])
        resource, _ = Resource.objects.get_or_create(url='test', defaults={
            'name': 'Test Resource'
        })
        consumer, _ = Consumer.objects.get_or_create(key='123', defaults={
            'name': 'Test',
            'description': 'Testing...'
        })
        token, _ = Token.objects.get_or_create(key='foo', token_type=Token.ACCESS, defaults={
            'consumer': consumer,
            'resource': resource,
            'secret': '',
            'user': user,
        })
        resp = auth.is_authenticated(request)
        self.assertEqual(resp, True)
        self.assertEqual(request.user.pk, user.pk)
