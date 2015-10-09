from __future__ import unicode_literals

import django
from django.conf import settings
from django.contrib.auth import get_user_model as django_get_user_model


__all__ = ['get_user_model', 'get_username_field', 'AUTH_USER_MODEL']

AUTH_USER_MODEL = settings.AUTH_USER_MODEL

get_user_model = django_get_user_model


def get_username_field():
    return get_user_model().USERNAME_FIELD


def get_module_name(meta):
    return meta.model_name

# commit_on_success replaced by atomic in Django >=1.8
atomic_decorator = getattr(django.db.transaction, 'atomic', None) or getattr(django.db.transaction, 'commit_on_success')
