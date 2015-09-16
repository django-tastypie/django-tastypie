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
