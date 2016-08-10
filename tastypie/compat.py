from __future__ import unicode_literals

import django
from django.conf import settings
from django.contrib.auth import get_user_model  # flake8: noqa

__all__ = ['get_user_model', 'get_username_field', 'AUTH_USER_MODEL']


AUTH_USER_MODEL = settings.AUTH_USER_MODEL


def get_username_field():
    return get_user_model().USERNAME_FIELD


def get_module_name(meta):
    return meta.model_name


atomic_decorator = django.db.transaction.atomic

# Compatability for salted vs unsalted CSRF tokens;
# Django 1.10's _sanitize_token also hashes it, so it can't be compared directly.
# Solution is to call _sanitize_token on both tokens, then unsalt or noop both
try:
    from django.middleware.csrf import _unsalt_cipher_token
    def unsalt_token(token):
        return _unsalt_cipher_token(token)
except ImportError:
    def unsalt_token(token):
        return token
