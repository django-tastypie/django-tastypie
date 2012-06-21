import email
import datetime
import time
from django.utils import dateformat
from tastypie.utils.timezone import make_aware, make_naive, aware_datetime

# Try to use dateutil for maximum date-parsing niceness. Fall back to
# hard-coded RFC2822 parsing if that's not possible.
try:
    from dateutil.parser import parse as mk_datetime
except ImportError:
    def mk_datetime(string):
        return make_aware(datetime.datetime.fromtimestamp(time.mktime(email.utils.parsedate(string))))

def format_datetime(dt):
    """
    RFC 2822 datetime formatter
    """
    return dateformat.format(make_naive(dt), 'r')

def format_date(d):
    """
    RFC 2822 date formatter
    """
    # workaround because Django's dateformat utility requires a datetime
    # object (not just date)
    dt = aware_datetime(d.year, d.month, d.day, 0, 0, 0)
    return dateformat.format(dt, 'j M Y')

def format_time(t):
    """
    RFC 2822 time formatter
    """
    # again, workaround dateformat input requirement
    dt = aware_datetime(2000, 1, 1, t.hour, t.minute, t.second)
    return dateformat.format(dt, 'H:i:s O')
