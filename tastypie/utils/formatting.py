import datetime
from django.utils import dateformat

# Try to use dateutil for maximum date-parsing niceness. Fall back to
# hard-coded RFC2822 parsing if that's not possible.
try:
    from dateutil.parser import parse as mk_datetime
except ImportError:
    def mk_datetime(string):
        return datetime.datetime.fromtimestamp(time.mktime(email.utils.parsedate(string)))

def format_datetime(dt):
    return dateformat.format(dt, 'r')

