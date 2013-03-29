import base64
import os
import time
import warnings
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpRequest
from django.test import TestCase
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication, SessionAuthentication, DigestAuthentication, OAuthAuthentication, MultiAuthentication
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
    fixtures = ['note_testdata.json']

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

    def test_check_active_false(self):
        auth = Authentication(require_active=False)
        user = User.objects.get(username='johndoe')
        self.assertTrue(auth.check_active(user))

        auth = Authentication(require_active=False)
        user = User.objects.get(username='bobdoe')
        self.assertTrue(auth.check_active(user))

    def test_check_active_true(self):
        auth = Authentication(require_active=True)
        user = User.objects.get(username='johndoe')
        self.assertTrue(auth.check_active(user))

        auth = Authentication(require_active=True)
        user = User.objects.get(username='bobdoe')
        self.assertFalse(auth.check_active(user))

        # Check the default.
        auth = Authentication()
        user = User.objects.get(username='bobdoe')
        self.assertFalse(auth.check_active(user))


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

    def test_check_active_true(self):
        auth = BasicAuthentication()
        request = HttpRequest()

        bob_doe = User.objects.get(username='bobdoe')
        bob_doe.set_password('pass')
        bob_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('bobdoe:pass')
        self.assertFalse(auth.is_authenticated(request))

    def test_check_active_false(self):
        auth = BasicAuthentication(require_active=False)
        request = HttpRequest()

        bob_doe = User.objects.get(username='bobdoe')
        bob_doe.set_password('pass')
        bob_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('bobdoe:pass')
        self.assertTrue(auth.is_authenticated(request))


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
        self.assertEqual(auth.get_identifier(request), 'johndoe')

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

    def test_check_active_true(self):
        auth = ApiKeyAuthentication()
        request = HttpRequest()

        bob_doe = User.objects.get(username='bobdoe')
        create_api_key(User, instance=bob_doe, created=True)
        request.META['HTTP_AUTHORIZATION'] = 'ApiKey bobdoe:%s' % bob_doe.api_key.key
        self.assertFalse(auth.is_authenticated(request))

    def test_check_active_false(self):
        auth = BasicAuthentication(require_active=False)
        request = HttpRequest()

        bob_doe = User.objects.get(username='bobdoe')
        create_api_key(User, instance=bob_doe, created=True)
        request.META['HTTP_AUTHORIZATION'] = 'ApiKey bobdoe:%s' % bob_doe.api_key.key
        self.assertTrue(auth.is_authenticated(request))


class SessionAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_is_authenticated(self):
        auth = SessionAuthentication()
        request = HttpRequest()
        request.method = 'POST'
        request.COOKIES = {
            settings.CSRF_COOKIE_NAME: 'abcdef1234567890abcdef1234567890'
        }

        # No CSRF token.
        request.META = {}
        self.assertFalse(auth.is_authenticated(request))

        # Invalid CSRF token.
        request.META = {
            'HTTP_X_CSRFTOKEN': 'abc123'
        }
        self.assertFalse(auth.is_authenticated(request))

        # Not logged in.
        request.META = {
            'HTTP_X_CSRFTOKEN': 'abcdef1234567890abcdef1234567890'
        }
        request.user = AnonymousUser()
        self.assertFalse(auth.is_authenticated(request))

        # Logged in.
        request.user = User.objects.get(username='johndoe')
        self.assertTrue(auth.is_authenticated(request))

        # Logged in (with GET & no token).
        request.method = 'GET'
        request.META = {}
        request.user = User.objects.get(username='johndoe')
        self.assertTrue(auth.is_authenticated(request))

        # Secure & wrong referrer.
        os.environ["HTTPS"] = "on"
        request.method = 'POST'
        request.META = {
            'HTTP_X_CSRFTOKEN': 'abcdef1234567890abcdef1234567890'
        }
        request.META['HTTP_HOST'] = 'example.com'
        request.META['HTTP_REFERER'] = ''
        self.assertFalse(auth.is_authenticated(request))

        # Secure & correct referrer.
        request.META['HTTP_REFERER'] = 'https://example.com/'
        self.assertTrue(auth.is_authenticated(request))

        os.environ["HTTPS"] = "off"

    def test_get_identifier(self):
        auth = SessionAuthentication()
        request = HttpRequest()

        # Not logged in.
        request.user = AnonymousUser()
        self.assertEqual(auth.get_identifier(request), '')

        # Logged in.
        request.user = User.objects.get(username='johndoe')
        self.assertEqual(auth.get_identifier(request), 'johndoe')


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

    def test_check_active_true(self):
        auth = DigestAuthentication()
        request = HttpRequest()

        bob_doe = User.objects.get(username='bobdoe')
        create_api_key(User, instance=bob_doe, created=True)
        auth_request = auth.is_authenticated(request)
        request.META['HTTP_AUTHORIZATION'] = python_digest.build_authorization_request(
            bob_doe.username,
            request.method,
            '/', # uri
            1,   # nonce_count
            digest_challenge=auth_request['WWW-Authenticate'],
            password=bob_doe.api_key.key
        )
        auth_request = auth.is_authenticated(request)
        self.assertFalse(auth_request)

    def test_check_active_false(self):
        auth = DigestAuthentication(require_active=False)
        request = HttpRequest()

        bob_doe = User.objects.get(username='bobdoe')
        create_api_key(User, instance=bob_doe, created=True)
        auth_request = auth.is_authenticated(request)
        request.META['HTTP_AUTHORIZATION'] = python_digest.build_authorization_request(
            bob_doe.username,
            request.method,
            '/', # uri
            1,   # nonce_count
            digest_challenge=auth_request['WWW-Authenticate'],
            password=bob_doe.api_key.key
        )
        auth_request = auth.is_authenticated(request)
        self.assertTrue(auth_request, True)


class OAuthAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def setUp(self):
        super(OAuthAuthenticationTestCase, self).setUp()

        self.request = HttpRequest()
        self.request.META['SERVER_NAME'] = 'testsuite'
        self.request.META['SERVER_PORT'] = '8080'
        self.request.REQUEST = self.request.GET = {}
        self.request.method = "GET"

        from oauth_provider.models import Consumer, Token, Resource
        self.user = User.objects.create_user('daniel', 'test@example.com', 'password')
        self.user_inactive = User.objects.get(username='bobdoe')
        self.resource, _ = Resource.objects.get_or_create(url='test', defaults={
            'name': 'Test Resource'
        })
        self.consumer, _ = Consumer.objects.get_or_create(key='123', defaults={
            'name': 'Test',
            'description': 'Testing...'
        })
        self.token, _ = Token.objects.get_or_create(key='foo', token_type=Token.ACCESS, defaults={
            'consumer': self.consumer,
            'resource': self.resource,
            'secret': '',
            'user': self.user,
        })
        self.token_inactive, _ = Token.objects.get_or_create(key='bar', token_type=Token.ACCESS, defaults={
            'consumer': self.consumer,
            'resource': self.resource,
            'secret': '',
            'user': self.user_inactive,
        })

    def test_is_authenticated(self):
        auth = OAuthAuthentication()

        # Invalid request.
        resp = auth.is_authenticated(self.request)
        self.assertEqual(resp.status_code, 401)

        # No username/api_key details should fail.
        self.request.REQUEST = self.request.GET = {
            'oauth_consumer_key': '123',
            'oauth_nonce': 'abc',
            'oauth_signature': '&',
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': 'foo',
        }
        self.request.META['Authorization'] = 'OAuth ' + ','.join([key+'='+value for key, value in self.request.REQUEST.items()])
        resp = auth.is_authenticated(self.request)
        self.assertEqual(resp, True)
        self.assertEqual(self.request.user.pk, self.user.pk)

    def test_check_active_true(self):
        auth = OAuthAuthentication()

        # No username/api_key details should fail.
        self.request.REQUEST = self.request.GET = {
            'oauth_consumer_key': '123',
            'oauth_nonce': 'abc',
            'oauth_signature': '&',
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': 'bar',
        }
        self.request.META['Authorization'] = 'OAuth ' + ','.join([key+'='+value for key, value in self.request.REQUEST.items()])
        resp = auth.is_authenticated(self.request)
        self.assertFalse(resp)

    def test_check_active_false(self):
        auth = OAuthAuthentication(require_active=False)

        # No username/api_key details should fail.
        self.request.REQUEST = self.request.GET = {
            'oauth_consumer_key': '123',
            'oauth_nonce': 'abc',
            'oauth_signature': '&',
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': 'bar',
        }
        self.request.META['Authorization'] = 'OAuth ' + ','.join([key+'='+value for key, value in self.request.REQUEST.items()])
        resp = auth.is_authenticated(self.request)
        self.assertTrue(resp)
        self.assertEqual(self.request.user.pk, self.user_inactive.pk)


class MultiAuthenticationTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_apikey_and_authentication_enforce_user(self):
        session_auth = SessionAuthentication()
        api_key_auth = ApiKeyAuthentication()
        auth = MultiAuthentication(api_key_auth, session_auth)
        john_doe = User.objects.get(username='johndoe')
        request1 = HttpRequest()
        request2 = HttpRequest()
        request3 = HttpRequest()

        request1.method = 'POST'
        request1.META = {
            'HTTP_X_CSRFTOKEN': 'abcdef1234567890abcdef1234567890'
        }
        request1.COOKIES = {
            settings.CSRF_COOKIE_NAME: 'abcdef1234567890abcdef1234567890'
        }
        request1.user = john_doe

        request2.POST['username'] = 'janedoe'
        request2.POST['api_key'] = 'invalid key'

        request3.method = 'POST'
        request3.META = {
            'HTTP_X_CSRFTOKEN': 'abcdef1234567890abcdef1234567890'
        }
        request3.COOKIES = {
            settings.CSRF_COOKIE_NAME: 'abcdef1234567890abcdef1234567890'
        }
        request3.user = john_doe
        request3.POST['username'] = 'janedoe'
        request3.POST['api_key'] = 'invalid key'

        #session auth should pass if since john_doe is logged in
        self.assertTrue(session_auth.is_authenticated(request1))
        #api key auth should fail because of invalid api key
        self.assertEqual(isinstance(api_key_auth.is_authenticated(request2), HttpUnauthorized), True)

        #multi auth shouldn't change users if api key auth fails
        #multi auth passes since session auth is valid
        self.assertEqual(request3.user.username, 'johndoe')
        self.assertTrue(auth.is_authenticated(request3))
        self.assertEqual(request3.user.username, 'johndoe')

    def test_apikey_and_authentication(self):
        auth = MultiAuthentication(ApiKeyAuthentication(), Authentication())
        request = HttpRequest()

        john_doe = User.objects.get(username='johndoe')

        # No username/api_key details should pass.
        self.assertEqual(auth.is_authenticated(request), True)

        # The identifier should be the basic auth stock.
        self.assertEqual(auth.get_identifier(request), 'noaddr_nohost')

        # Wrong username details.
        request = HttpRequest()
        request.GET['username'] = 'foo'
        self.assertEqual(auth.is_authenticated(request), True)
        self.assertEqual(auth.get_identifier(request), 'noaddr_nohost')

        # No api_key.
        request = HttpRequest()
        request.GET['username'] = 'daniel'
        self.assertEqual(auth.is_authenticated(request), True)
        self.assertEqual(auth.get_identifier(request), 'noaddr_nohost')

        # Wrong user/api_key.
        request = HttpRequest()
        request.GET['username'] = 'daniel'
        request.GET['api_key'] = 'foo'
        self.assertEqual(auth.is_authenticated(request), True)
        self.assertEqual(auth.get_identifier(request), 'noaddr_nohost')

        request = HttpRequest()
        request.GET['username'] = 'johndoe'
        request.GET['api_key'] = john_doe.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)
        self.assertEqual(auth.get_identifier(request), 'johndoe')


    def test_apikey_and_basic_auth(self):
        auth = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication())
        request = HttpRequest()
        john_doe = User.objects.get(username='johndoe')

        # No API Key or HTTP Basic auth details should fail.
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Basic Auth still returns appropriately.
        self.assertEqual(auth.is_authenticated(request)['WWW-Authenticate'], 'Basic Realm="django-tastypie"')

        # API Key Auth works.
        request = HttpRequest()
        request.GET['username'] = 'johndoe'
        request.GET['api_key'] = john_doe.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)
        self.assertEqual(auth.get_identifier(request), 'johndoe')


        # Basic Auth works.
        request = HttpRequest()
        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('johndoe:pass')
        self.assertEqual(auth.is_authenticated(request), True)


