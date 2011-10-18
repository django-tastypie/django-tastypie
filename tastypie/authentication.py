from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from piecrust.authentication import Authentication
from piecrust.authentication import BasicAuthentication as PiecrustBasicAuthentication
from piecrust.authentication import ApiKeyAuthentication as PiecrustApiKeyAuthentication
from piecrust.authentication import DigestAuthentication as PiecrustDigestAuthentication
from piecrust.exceptions import ImproperlyConfigured, Unauthorized
from tastypie.models import ApiKey
try:
    import oauth2
except ImportError:
    oauth2 = None
try:
    import oauth_provider
except ImportError:
    oauth_provider = None


class BasicAuthentication(PiecrustBasicAuthentication):
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
    realm = 'django-tastypie'

    def check_credentials(self, username, password):
        """
        Checks a user's basic auth credentials against the current
        Django auth backend.
        """
        if self.backend:
            user = self.backend.authenticate(username=username, password=password)
        else:
            user = authenticate(username=username, password=password)

        if not user:
            raise Unauthorized()

        return user


class ApiKeyAuthentication(PiecrustApiKeyAuthentication):
    """
    Handles API key auth, in which a user provides a username & API key.

    Uses the ``ApiKey`` model that ships with tastypie. If you wish to use
    a different model, override the ``get_key`` method to perform the key check
    as suits your needs.
    """
    def check_credentials(self, username, api_key):
        """
        Finds the user and checks their API key.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        try:
            user = User.objects.get(username=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            raise Unauthorized("User does not exist.")

        try:
            ApiKey.objects.get(user=user, key=api_key)
        except ApiKey.DoesNotExist:
            raise Unauthorized("Api key does not exist.")

        return user


class DigestAuthentication(PiecrustDigestAuthentication):
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
    secret_key = getattr(settings, 'SECRET_KEY', '')
    realm = 'django-tastypie'

    def check_credentials(self, request, digest_response, username):
        """
        Finds the user and checks their API key.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        try:
            user = User.objects.get(username=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            raise Unauthorized("No such user.")

        try:
            key = ApiKey.objects.get(user=user)
        except ApiKey.DoesNotExist:
            raise Unauthorized("No such API key.")

        expected = self.calculate_request_digest(request, digest_response, username, key.key)

        if not digest_response.response == expected:
            raise Unauthorized("Digests did not match.")

        return user


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
        from oauth_provider.store import store

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
