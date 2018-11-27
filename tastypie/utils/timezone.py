from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.utils import timezone


def make_aware(value):
    if settings.USE_TZ and timezone.is_naive(value):
        default_tz = timezone.get_default_timezone()
        value = timezone.make_aware(value, default_tz)
    return value


def make_naive(value):
    if settings.USE_TZ and timezone.is_aware(value):
        default_tz = timezone.get_default_timezone()
        value = timezone.make_naive(value, default_tz)
    return value


def now():
    d = timezone.now()

    if d.tzinfo:
        return timezone.localtime(d)

    return d


def aware_date(*args, **kwargs):
    return make_aware(datetime.date(*args, **kwargs))


def aware_datetime(*args, **kwargs):
    return make_aware(datetime.datetime(*args, **kwargs))
