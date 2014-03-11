from __future__ import unicode_literals
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import django

__all__ = ['User', 'AUTH_USER_MODEL']

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
AUTH_USERNAME_FIELD = getattr(settings, 'AUTH_USERNAME_FIELD', 'username')

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        username_field = User.USERNAME_FIELD
    except ImproperlyConfigured:
        # The the users model might not be read yet.
        # This can happen is when setting up the create_api_key signal, in your
        # custom user module.
        # Assume the defaults
        User = AUTH_USER_MODEL
        username_field = AUTH_USERNAME_FIELD
else:
    from django.contrib.auth.models import User
    username_field = 'username'
