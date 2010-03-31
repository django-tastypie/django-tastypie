import base64
from django.contrib.auth.backends import ModelBackend


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
    Handles HTTP Basic auth against ``django.contrib.auth.models.User``.
    """
    def __init__(self):
        self.backend = ModelBackend()
    
    def is_authenticated(self, request, **kwargs):
        if not request.META.get('HTTP_AUTHORIZATION'):
            return False
        
        try:
            user_pass = base64.b64decode(request.META['HTTP_AUTHORIZATION'])
        except:
            return False
        
        bits = user_pass.split(':')
        
        if len(bits) != 2:
            return False
        
        user = self.backend.authenticate(username=bits[0], password=bits[1])
        
        if user is None:
            return False
        
        return True
