import base64
import hmac
import time
import uuid

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _
from tastypie.http import HttpUnauthorized

try:
    from hashlib import sha1
except ImportError:
    import sha
    sha1 = sha.sha

try:
    import python_digest
except ImportError:
    python_digest = None

try:
    import oauth2
except ImportError:
    oauth2 = None

try:
    import oauth_provider
except ImportError:
    oauth_provider = None


class Authentication(object):
    """
    A simple base class to establish the protocol for auth.

    By default, this indicates the user is always authenticated.
    """
    def is_authenticated(self, request, **kwargs):
        """
        Identifies if the user is authenticated to continue or not.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        return True

    def get_identifier(self, request):
        """
        Provides a unique string identifier for the requestor.

        This implementation returns a combination of IP address and hostname.
        """
        return "%s_%s" % (request.META.get('REMOTE_ADDR', 'noaddr'), request.META.get('REMOTE_HOST', 'nohost'))


class BasicAuthentication(Authentication):
    """
    Handles HTTP Basic auth against a specific auth backend if provided,
    or against all configured authentication backends using the
    ``authenticate`` method from ``django.contrib.auth``.

    Optional keyword arguments:

    ``backend``
        If specified, use a specific ``django.contrib.auth`` backend instead
        of checking all backends specified in the ``AUTHENTICATION_BACKENDS``
        setting.
    ``realm``
        The realm to use in the ``HttpUnauthorized`` response.  Default:
        ``django-tastypie``.
    """
    def __init__(self, backend=None, realm='django-tastypie'):
        self.backend = backend
        self.realm = realm

    def _unauthorized(self):
        response = HttpUnauthorized()
        # FIXME: Sanitize realm.
        response['WWW-Authenticate'] = 'Basic Realm="%s"' % self.realm
        return response

    def is_authenticated(self, request, **kwargs):
        """
        Checks a user's basic auth credentials against the current
        Django auth backend.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        if not request.META.get('HTTP_AUTHORIZATION'):
            return self._unauthorized()

        try:
            (auth_type, data) = request.META['HTTP_AUTHORIZATION'].split()
            if auth_type != 'Basic':
                return self._unauthorized()
            user_pass = base64.b64decode(data)
        except:
            return self._unauthorized()

        bits = user_pass.split(':', 1)

        if len(bits) != 2:
            return self._unauthorized()

        if self.backend:
            user = self.backend.authenticate(username=bits[0], password=bits[1])
        else:
            user = authenticate(username=bits[0], password=bits[1])

        if user is None:
            return self._unauthorized()

        request.user = user
        return True

    def get_identifier(self, request):
        """
        Provides a unique string identifier for the requestor.

        This implementation returns the user's basic auth username.
        """
        return request.META.get('REMOTE_USER', 'nouser')


class ApiKeyAuthentication(Authentication):
    """
    Handles API key auth, in which a user provides a username & API key.

    Uses the ``ApiKey`` model that ships with tastypie. If you wish to use
    a different model, override the ``get_key`` method to perform the key check
    as suits your needs.
    """
    def _unauthorized(self):
        return HttpUnauthorized()

    def is_authenticated(self, request, **kwargs):
        """
        Finds the user and checks their API key.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        from django.contrib.auth.models import User

        username = request.GET.get('username') or request.POST.get('username')
        api_key = request.GET.get('api_key') or request.POST.get('api_key')

        if not username or not api_key:
            return self._unauthorized()

        try:
            user = User.objects.get(username=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return self._unauthorized()

        request.user = user
        return self.get_key(user, api_key)

    def get_key(self, user, api_key):
        """
        Attempts to find the API key for the user. Uses ``ApiKey`` by default
        but can be overridden.
        """
        from tastypie.models import ApiKey

        try:
            ApiKey.objects.get(user=user, key=api_key)
        except ApiKey.DoesNotExist:
            return self._unauthorized()

        return True

    def get_identifier(self, request):
        """
        Provides a unique string identifier for the requestor.

        This implementation returns the user's username.
        """
        return request.REQUEST.get('username', 'nouser')


class DigestAuthentication(Authentication):
    """
    Handles HTTP Digest auth against a specific auth backend if provided,
    or against all configured authentication backends using the
    ``authenticate`` method from ``django.contrib.auth``. However, instead of
    the user's password, their API key should be used.

    Optional keyword arguments:

    ``backend``
        If specified, use a specific ``django.contrib.auth`` backend instead
        of checking all backends specified in the ``AUTHENTICATION_BACKENDS``
        setting.
    ``realm``
        The realm to use in the ``HttpUnauthorized`` response.  Default:
        ``django-tastypie``.
    """
    def __init__(self, backend=None, realm='django-tastypie'):
        self.backend = backend
        self.realm = realm

        if python_digest is None:
            raise ImproperlyConfigured("The 'python_digest' package could not be imported. It is required for use with the 'DigestAuthentication' class.")

    def _unauthorized(self):
        response = HttpUnauthorized()
        new_uuid = uuid.uuid4()
        opaque = hmac.new(str(new_uuid), digestmod=sha1).hexdigest()
        response['WWW-Authenticate'] = python_digest.build_digest_challenge(time.time(), getattr(settings, 'SECRET_KEY', ''), self.realm, opaque, False)
        return response

    def is_authenticated(self, request, **kwargs):
        """
        Finds the user and checks their API key.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        if not request.META.get('HTTP_AUTHORIZATION'):
            return self._unauthorized()

        try:
            (auth_type, data) = request.META['HTTP_AUTHORIZATION'].split(' ', 1)

            if auth_type != 'Digest':
                return self._unauthorized()
        except:
            return self._unauthorized()

        digest_response = python_digest.parse_digest_credentials(request.META['HTTP_AUTHORIZATION'])

        # FIXME: Should the nonce be per-user?
        if not python_digest.validate_nonce(digest_response.nonce, getattr(settings, 'SECRET_KEY', '')):
            return self._unauthorized()

        user = self.get_user(digest_response.username)
        api_key = self.get_key(user)

        if user is False or api_key is False:
            return self._unauthorized()

        expected = python_digest.calculate_request_digest(
            request.method,
            python_digest.calculate_partial_digest(digest_response.username, self.realm, api_key),
            digest_response)

        if not digest_response.response == expected:
            return self._unauthorized()

        request.user = user
        return True

    def get_user(self, username):
        from django.contrib.auth.models import User

        try:
            user = User.objects.get(username=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return False

        return user

    def get_key(self, user):
        """
        Attempts to find the API key for the user. Uses ``ApiKey`` by default
        but can be overridden.

        Note that this behaves differently than the ``ApiKeyAuthentication``
        method of the same name.
        """
        from tastypie.models import ApiKey

        try:
            key = ApiKey.objects.get(user=user)
        except ApiKey.DoesNotExist:
            return False

        return key.key

    def get_identifier(self, request):
        """
        Provides a unique string identifier for the requestor.

        This implementation returns the user's username.
        """
        if hasattr(request, 'user'):
            if hasattr(request.user, 'username'):
                return request.user.username

        return 'nouser'


class OAuthAuthentication(Authentication):
    """
    Handles OAuth, which checks a user's credentials against a separate service.
    Currently verifies against OAuth 1.0a services.

    This does *NOT* provide OAuth authentication in your API, strictly
    consumption.
    """
    def __init__(self):
        super(OAuthAuthentication, self).__init__()

        if oauth2 is None:
            raise ImproperlyConfigured("The 'python-oauth2' package could not be imported. It is required for use with the 'OAuthAuthentication' class.")

        if oauth_provider is None:
            raise ImproperlyConfigured("The 'django-oauth-plus' package could not be imported. It is required for use with the 'OAuthAuthentication' class.")

    def is_authenticated(self, request, **kwargs):
        from oauth_provider.store import store, InvalidTokenError

        if self.is_valid_request(request):
            oauth_request = oauth_provider.utils.get_oauth_request(request)
            consumer = store.get_consumer(request, oauth_request, oauth_request.get_parameter('oauth_consumer_key'))

            try:
                token = store.get_access_token(request, oauth_request, consumer, oauth_request.get_parameter('oauth_token'))
            except oauth_provider.store.InvalidTokenError:
                return oauth_provider.utils.send_oauth_error(oauth2.Error(_('Invalid access token: %s') % oauth_request.get_parameter('oauth_token')))

            try:
                self.validate_token(request, consumer, token)
            except oauth2.Error, e:
                return oauth_provider.utils.send_oauth_error(e)

            if consumer and token:
                request.user = token.user
                return True

            return oauth_provider.utils.send_oauth_error(oauth2.Error(_('You are not allowed to access this resource.')))

        return oauth_provider.utils.send_oauth_error(oauth2.Error(_('Invalid request parameters.')))

    def is_in(self, params):
        """
        Checks to ensure that all the OAuth parameter names are in the
        provided ``params``.
        """
        from oauth_provider.consts import OAUTH_PARAMETERS_NAMES
        for param_name in OAUTH_PARAMETERS_NAMES:
            if param_name not in params:
                return False

        return True

    def is_valid_request(self, request):
        """
        Checks whether the required parameters are either in the HTTP
        ``Authorization`` header sent by some clients (the preferred method
        according to OAuth spec) or fall back to ``GET/POST``.
        """
        auth_params = request.META.get("HTTP_AUTHORIZATION", [])
        return self.is_in(auth_params) or self.is_in(request.REQUEST)

    def validate_token(self, request, consumer, token):
        oauth_server, oauth_request = oauth_provider.utils.initialize_server_request(request)
        return oauth_server.verify_request(oauth_request, consumer, token)
