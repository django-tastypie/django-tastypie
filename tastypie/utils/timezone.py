import datetime
from django.conf import settings
import six
try:
    import pytz
except ImportError:
    pytz = None

try:
    from django.utils import timezone
    from django.utils.timezone import get_default_timezone, is_naive, is_aware, make_naive as _make_naive, make_aware as _make_aware

    make_aware = lambda value, timezone=None: _make_aware(value, timezone or get_default_timezone())
    make_naive = lambda value, timezone=None: _make_naive(value, timezone or get_default_timezone())

    def now():
        return timezone.localtime(timezone.now())

except ImportError:
    def get_default_timezone():
        tzname = getattr(settings, 'TIME_ZONE', None)
        if pytz is not None:
            tzinfo = pytz.timezone(tzname).localize(pytz.datetime.datetime.now()).tzinfo
            return tzinfo
        try:
            # This is a proxy for the time.tzinfo proxy, using ('CST', 'CDT')
            # and the os.environ['TZ'] for setting the timezone.  This behaves
            # very different from the pytz implementation of timezones.
            from django.utils.tzinfo import LocalTimezone
            from datetime import datetime
            tzinfo = LocalTimezone(datetime.now())
            return tzinfo
        except:
            # using time.tzset() with an olson timezone ('America/Chicago') is
            # only expected to work on a *nix system, so this may fail in some
            # strainge way on windows.
            return None

    def make_aware(value, timezone=None):
        """
        Makes a naive datetime.datetime in a given time zone aware.
        """
        if timezone is None:
            timezone = get_default_timezone()
        if hasattr(timezone, 'localize'):
            # available for pytz time zones
            return timezone.localize(value, is_dst=None)
        else:
            # may be wrong around DST changes
            return value.replace(tzinfo=timezone)

    def make_naive(value, timezone=None):
        """
        Makes an aware datetime.datetime naive in a given time zone.
        """
        if timezone is None:
            timezone = get_default_timezone()
        value = value.astimezone(timezone)
        if hasattr(timezone, 'normalize'):
            # available for pytz time zones
            value = timezone.normalize(value)
        return value.replace(tzinfo=None)
        def is_naive(dt):
            """Straight copy of 1.5's is_naive"""
            return value.tzinfo is None or value.tzinfo.utcoffset(value) is None

    now = lambda : make_aware(datetime.datetime.now())



def is_aware(value):
    """
    Determines if a given datetime.datetime is aware.

    The logic is described in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo
    """
    return value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None

def is_naive(value):
    """
    Determines if a given datetime.datetime is naive.

    The logic is described in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo
    """
    return value.tzinfo is None or value.tzinfo.utcoffset(value) is None



def aware_date(*args, **kwargs):
    return make_aware(datetime.date(*args, **kwargs))

def aware_datetime(*args, **kwargs):
    return make_aware(datetime.datetime(*args, **kwargs))
