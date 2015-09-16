from django.http import HttpRequest
from django.test import TestCase

from tastypie.authentication import ApiKeyAuthentication
from tastypie.http import HttpUnauthorized
from tastypie.models import ApiKey, create_api_key

from customuser.models import CustomUser


class CustomUserTestCase(TestCase):
    fixtures = ['customuser.json']

    def setUp(self):
        super(CustomUserTestCase, self).setUp()
        ApiKey.objects.all().delete()

    def test_is_authenticated_get_params(self):
        auth = ApiKeyAuthentication()
        request = HttpRequest()

        # Simulate sending the signal.
        john_doe = CustomUser.objects.get(pk=1)
        create_api_key(CustomUser, instance=john_doe, created=True)

        # No username/api_key details should fail.
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Wrong username (email) details.
        request.GET['username'] = 'foo@bar.com'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # No api_key.
        request.GET['username'] = john_doe.email
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Wrong user/api_key.
        request.GET['username'] = john_doe.email
        request.GET['api_key'] = 'foo'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Correct user/api_key.
        ApiKey.objects.all().delete()
        create_api_key(CustomUser, instance=john_doe, created=True)
        request.GET['username'] = john_doe.email
        request.GET['api_key'] = john_doe.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)
        self.assertEqual(auth.get_identifier(request), john_doe.email)
