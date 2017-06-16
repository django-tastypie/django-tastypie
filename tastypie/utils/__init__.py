from tastypie.utils.dict import dict_strip_unicode_keys  # flake8: noqa
from tastypie.utils.formatting import mk_datetime, format_datetime, format_date, format_time  # flake8: noqa
from tastypie.utils.urls import trailing_slash  # flake8: noqa
from tastypie.utils.validate_jsonp import is_valid_jsonp_callback_value  # flake8: noqa
from tastypie.utils.timezone import now, make_aware, make_naive, aware_date, aware_datetime  # flake8: noqa


def string_to_python(value):
    if value in ('true', 'True', True):
        value = True
    elif value in ('false', 'False', False):
        value = False
    elif value in ('nil', 'none', 'None', None):
        value = None
    return value
