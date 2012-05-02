import time
from urlparse import urlparse
from django.conf import settings
from django.test import TestCase
from django.test.client import FakePayload, Client
from tastypie.serializers import Serializer


class TestApiClient(object):
    def __init__(self, serializer=None):
        self.client = Client()
        self.serializer = serializer

        if not self.serializer:
            self.serializer = Serializer()

    def get_content_type(self, short_format):
        return self.serializer.content_types.get(short_format, 'json')

    def get(self, uri, format='json', data=None, authentication=None, **kwargs):
        content_type = self.get_content_type(format)
        kwargs['HTTP_ACCEPT'] = content_type

        # GET & DELETE are the only times we don't serialize the data.
        if data is not None:
            kwargs['data'] = data

        if authentication is not None:
            kwargs['HTTP_AUTHORIZATION'] = authentication

        return self.client.get(uri, **kwargs)

    def post(self, uri, format='json', data=None, authentication=None, **kwargs):
        content_type = self.get_content_type(format)
        kwargs['content_type'] = content_type

        if data is not None:
            kwargs['data'] = self.serializer.serialize(data, format=content_type)

        if authentication is not None:
            kwargs['HTTP_AUTHORIZATION'] = authentication

        return self.client.post(uri, **kwargs)

    def put(self, uri, format='json', data=None, authentication=None, **kwargs):
        content_type = self.get_content_type(format)
        kwargs['content_type'] = content_type

        if data is not None:
            kwargs['data'] = self.serializer.serialize(data, format=content_type)

        if authentication is not None:
            kwargs['HTTP_AUTHORIZATION'] = authentication

        return self.client.put(uri, **kwargs)

    def patch(self, uri, format='json', data=None, authentication=None, **kwargs):
        content_type = self.get_content_type(format)
        kwargs['content_type'] = content_type

        if data is not None:
            kwargs['data'] = self.serializer.serialize(data, format=content_type)

        if authentication is not None:
            kwargs['HTTP_AUTHORIZATION'] = authentication

        # This hurts because Django doesn't support PATCH natively.
        parsed = urlparse(uri)
        r = {
            'CONTENT_LENGTH': len(kwargs['data']),
            'CONTENT_TYPE': content_type,
            'PATH_INFO': self.client._get_path(parsed),
            'QUERY_STRING': parsed[4],
            'REQUEST_METHOD': 'PATCH',
            'wsgi.input': FakePayload(kwargs['data']),
        }
        r.update(kwargs)
        return self.client.request(**r)

    def delete(self, uri, format='json', data=None, authentication=None, **kwargs):
        content_type = self.get_content_type(format)
        kwargs['content_type'] = content_type

        # GET & DELETE are the only times we don't serialize the data.
        if data is not None:
            kwargs['data'] = data

        if authentication is not None:
            kwargs['HTTP_AUTHORIZATION'] = authentication

        return self.client.delete(uri, **kwargs)


class ResourceTestCase(TestCase):
    """
    A useful base class for the start of testing Tastypie APIs.
    """
    def setUp(self):
        super(ResourceTestCase, self).setUp()
        self.serializer = Serializer()
        self.api_client = TestApiClient()

    def get_credentials(self):
        """
        A convenience method for the user as a way to shorten up the
        often repetitious calls to create the same authentication.

        Raises ``NotImplementedError`` by default.

        Usage::

            class MyResourceTestCase(ResourceTestCase):
                def get_credentials(self):
                    return self.create_basic('daniel', 'pass')

                # Then the usual tests...

        """
        raise NotImplementedError("You must return the class for your Resource to test.")

    def create_basic(self, username, password):
        """
        Creates the HTTP ``Authorization`` header for use with BASIC Auth.
        """
        import base64
        return 'Basic %s' % base64.b64encode(':'.join([username, password]))

    def create_apikey(self, username, api_key):
        return 'ApiKey %s:%s' % (username, api_key)

    def create_digest(self, username, api_key, method, uri):
        from tastypie.authentication import hmac, sha1, uuid, python_digest

        new_uuid = uuid.uuid4()
        opaque = hmac.new(str(new_uuid), digestmod=sha1).hexdigest()
        return python_digest.build_authorization_request(
            username,
            method.upper(),
            uri,
            1, # nonce_count
            digest_challenge=python_digest.build_digest_challenge(time.time(), getattr(settings, 'SECRET_KEY', ''), 'django-tastypie', opaque, False),
            password=api_key
        )

    def create_oauth(self, user):
        from oauth_provider.models import Consumer, Token, Resource

        # Necessary setup for ``oauth_provider``.
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

        # Then generate the header.
        oauth_data = {
            'oauth_consumer_key': '123',
            'oauth_nonce': 'abc',
            'oauth_signature': '&',
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': 'foo',
        }
        return 'OAuth %s' % ','.join([key+'='+value for key, value in oauth_data.items()])

    def assertHttpOK(self, resp):
        return self.assertEqual(resp.status_code, 200)

    def assertHttpCreated(self, resp):
        return self.assertEqual(resp.status_code, 201)

    def assertHttpAccepted(self, resp):
       return self.assertTrue(resp.status_code in [202, 204])

    def assertHttpMultipleChoices(self, resp):
        return self.assertEqual(resp.status_code, 300)

    def assertHttpSeeOther(self, resp):
        return self.assertEqual(resp.status_code, 303)

    def assertHttpNotModified(self, resp):
        return self.assertEqual(resp.status_code, 304)

    def assertHttpBadRequest(self, resp):
        return self.assertEqual(resp.status_code, 400)

    def assertHttpUnauthorized(self, resp):
        return self.assertEqual(resp.status_code, 401)

    def assertHttpForbidden(self, resp):
        return self.assertEqual(resp.status_code, 403)

    def assertHttpNotFound(self, resp):
        return self.assertEqual(resp.status_code, 404)

    def assertHttpMethodNotAllowed(self, resp):
        return self.assertEqual(resp.status_code, 405)

    def assertHttpConflict(self, resp):
        return self.assertEqual(resp.status_code, 409)

    def assertHttpGone(self, resp):
        return self.assertEqual(resp.status_code, 410)

    def assertHttpApplicationError(self, resp):
        return self.assertEqual(resp.status_code, 500)

    def assertHttpNotImplemented(self, resp):
        return self.assertEqual(resp.status_code, 501)

    def assertValidJSON(self, data):
        # Just try the load. If it throws an exception, the test case will fail.
        self.serializer.from_json(data)

    def assertValidXML(self, data):
        # Just try the load. If it throws an exception, the test case will fail.
        self.serializer.from_xml(data)

    def assertValidYAML(self, data):
        # Just try the load. If it throws an exception, the test case will fail.
        self.serializer.from_yaml(data)

    def assertValidPlist(self, data):
        # Just try the load. If it throws an exception, the test case will fail.
        self.serializer.from_plist(data)

    def assertValidJSONResponse(self, resp):
        self.assertHttpOK(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        self.assertValidJSON(resp.content)

    def assertValidXMLResponse(self, resp):
        self.assertHttpOK(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/xml'))
        self.assertValidXML(resp.content)

    def assertValidYAMLResponse(self, resp):
        self.assertHttpOK(resp)
        self.assertTrue(resp['Content-Type'].startswith('text/yaml'))
        self.assertValidYAML(resp.content)

    def assertValidPlistResponse(self, resp):
        self.assertHttpOK(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/x-plist'))
        self.assertValidPlist(resp.content)

    def deserialize(self, resp):
        return self.serializer.deserialize(resp.content, format=resp['Content-Type'])

    def serialize(self, data, format='application/json'):
        return self.serializer.serialize(data, format=format)

    def assertKeys(self, data, expected):
        self.assertEqual(sorted(data.keys()), sorted(expected))
