from __future__ import unicode_literals

import django
from django.conf import settings
from django.contrib.auth import get_user_model  # noqa

try:
    from django.urls import NoReverseMatch, reverse, Resolver404, get_script_prefix  # noqa
except ImportError:  # 1.8 backwards compat
    from django.core.urlresolvers import NoReverseMatch, reverse, Resolver404, get_script_prefix  # noqa


AUTH_USER_MODEL = settings.AUTH_USER_MODEL


def is_authenticated(user):
    """
    Django is changing User.is_authenticated into a property.  Calling it
    will be deprecated by Django 2.0 and a warning in 1.10+.
    """
    if django.VERSION < (1, 10):
        return bool(user.is_authenticated())
    return bool(user.is_authenticated)


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


# force_text deprecated in 2.2, removed in 3.0
# note that in 1.1.x, force_str and force_text both exist, but force_str behaves
# much differently on python 3 than python 2.
if django.VERSION < (2, 2):
    from django.utils.encoding import force_text as force_str  # noqa
else:
    from django.utils.encoding import force_str  # noqa
