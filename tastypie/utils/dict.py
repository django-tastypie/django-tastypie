from django.utils import six
from django.utils.encoding import smart_bytes


def dict_strip_unicode_keys(uni_dict):
    """
    Converts a dict of unicode keys into a dict of ascii keys.

    Useful for converting a dict to a kwarg-able format.
    """
    if six.PY3:
        return uni_dict

    return dict([(smart_bytes(key), value,) for key, value in uni_dict.items()])
