from __future__ import unicode_literals
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import django

__all__ = ['User', 'AUTH_USER_MODEL']

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    username_field = User.USERNAME_FIELD
except ImproperlyConfigured:
    # The the users model might not be read yet.
    # This can happen is when setting up the create_api_key signal, in your
    # custom user module.
    User = None
