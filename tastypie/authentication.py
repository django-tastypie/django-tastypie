import base64
from django.contrib.auth import authenticate
from http import HttpUnauthorized


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
        if not request.META.get('HTTP_AUTHORIZATION'):
            return self._unauthorized()
        
        try:
            (auth_type, data) = request.META['HTTP_AUTHORIZATION'].split()
            if auth_type != 'Basic':
                return self._unauthorized()
            user_pass = base64.b64decode(data)
        except:
            return self._unauthorized()

        bits = user_pass.split(':')
        
        if len(bits) != 2:
            return self._unauthorized()

        if self.backend:
            user = self.backend.authenticate(username=bits[0], password=bits[1])
        else:
            user = authenticate(username=bits[0], password=bits[1])

        # FIXME: log in and check for request.user on future requests?

        if user is None:
            return self._unauthorized()
        
        return True
