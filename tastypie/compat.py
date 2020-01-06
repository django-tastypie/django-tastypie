import django
from django.conf import settings
from django.contrib.auth import get_user_model  # noqa
from django.middleware.csrf import _unsalt_cipher_token


AUTH_USER_MODEL = settings.AUTH_USER_MODEL


def get_username_field():
    return get_user_model().USERNAME_FIELD


def get_module_name(meta):
    return meta.model_name


def unsalt_token(token):
    return _unsalt_cipher_token(token)


# force_text deprecated in 2.2, removed in 3.0
# note that in 1.1.x, force_str and force_text both exist, but force_str behaves
# much differently on python 3 than python 2.
if django.VERSION < (2, 2):
    from django.utils.encoding import force_text as force_str  # noqa
else:
    from django.utils.encoding import force_str  # noqa
