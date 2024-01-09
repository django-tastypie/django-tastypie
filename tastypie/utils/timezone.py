import datetime
from django.conf import settings
from django.utils import timezone as dj_timezone
from datetime import timezone


def make_aware(value):
    if settings.USE_TZ and dj_timezone.is_naive(value):
        default_tz = dj_timezone.get_default_timezone()
        value = dj_timezone.make_aware(value, default_tz)
    return value


def make_naive(value):
    if settings.USE_TZ and dj_timezone.is_aware(value):
        default_tz = dj_timezone.get_default_timezone()
        value = dj_timezone.make_naive(value, default_tz)
    return value


def make_naive_utc(value):
    """
    Translate a datetime to UTC, then strip TZ info; useful as a last step before creating the
    Retry-After header.
    """
    utc_value = dj_timezone.localtime(value, timezone.utc)
    return dj_timezone.make_naive(utc_value)


def now():
    d = dj_timezone.now()

    if d.tzinfo:
        return dj_timezone.localtime(d)

    return d


def aware_date(*args, **kwargs):
    return make_aware(datetime.date(*args, **kwargs))


def aware_datetime(*args, **kwargs):
    return make_aware(datetime.datetime(*args, **kwargs))
