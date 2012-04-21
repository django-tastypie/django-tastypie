import datetime
from django.conf import settings

try:
    from django.utils import timezone

    def make_aware(value):
        if getattr(settings, "USE_TZ", False) and timezone.is_naive(value):
            default_tz = timezone.get_default_timezone()
            value = timezone.make_aware(value, default_tz)
        return value

    def make_naive(value):
        if getattr(settings, "USE_TZ", False) and timezone.is_aware(value):
            default_tz = timezone.get_default_timezone()
            value = timezone.make_naive(value, default_tz)
        return value

    def now():
        return timezone.localtime(timezone.now())

except ImportError:
    now = datetime.datetime.now
    make_aware = make_naive = lambda x: x

def aware_date(*args, **kwargs):
    return make_aware(datetime.date(*args, **kwargs))

def aware_datetime(*args, **kwargs):
    return make_aware(datetime.datetime(*args, **kwargs))
