from __future__ import unicode_literals
from django.conf import settings
import django

__all__ = ['get_user_model', 'get_username_field', 'AUTH_USER_MODEL']

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    def get_user_model():
        from django.contrib.auth import get_user_model as django_get_user_model

        return django_get_user_model()

    def get_username_field():
        return get_user_model().USERNAME_FIELD
else:
    def get_user_model():
        from django.contrib.auth.models import User

        return User

    def get_username_field():
        return 'username'
