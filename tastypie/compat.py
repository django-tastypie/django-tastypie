from __future__ import unicode_literals

import django
from django.conf import settings
from django.contrib.auth import get_user_model  # noqa

try:
    from django.urls import NoReverseMatch, reverse, Resolver404, get_script_prefix  # noqa
except ImportError:  # 1.8 backwards compat
    from django.core.urlresolvers import NoReverseMatch, reverse, Resolver404, get_script_prefix  # noqa


AUTH_USER_MODEL = settings.AUTH_USER_MODEL


def get_username_field():
    return get_user_model().USERNAME_FIELD


def get_module_name(meta):
    return meta.model_name


def is_ajax(request):
    """
    Handle multiple ways of detecting an ajax request.  Probably nearly useless.
    """
    if hasattr(request, 'is_ajax'):
        return request.is_ajax()
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


atomic_decorator = django.db.transaction.atomic

# force_text deprecated in 2.2, removed in 3.0
# note that in 1.1.x, force_str and force_text both exist, but force_str behaves
# much differently on python 3 than python 2.
if django.VERSION < (2, 2):
    from django.utils.encoding import force_text as force_str  # noqa
else:
    from django.utils.encoding import force_str  # noqa


compare_sanitized_tokens = None

# django 4.0
try:
    from django.middleware.csrf import _does_token_match, InvalidTokenFormat
    compare_sanitized_tokens = _does_token_match
except ImportError:
    pass


# django 3.2
if compare_sanitized_tokens is None:
    try:
        from django.middleware.csrf import _compare_masked_tokens
        compare_sanitized_tokens = _compare_masked_tokens
        class InvalidTokenFormat(Exception):  # noqa
            pass
    except ImportError:
        pass

# django 2.2
if compare_sanitized_tokens is None:
    try:
        from django.middleware.csrf import _unsalt_cipher_token, constant_time_compare

        def compare_sanitized_tokens(request_csrf_token, csrf_token):
            return constant_time_compare(_unsalt_cipher_token(request_csrf_token),
                                         _unsalt_cipher_token(csrf_token))

        class InvalidTokenFormat(Exception):  # noqa
            pass
    except ImportError:  # pragma: no cover
        raise ImportError("Couldn't find a way to compare csrf tokens safely")  # pragma: no cover
