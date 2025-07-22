from django.utils.encoding import smart_bytes


def dict_strip_unicode_keys(uni_dict):
    """
    Converts a dict of unicode keys into a dict of ascii keys.

    Useful for converting a dict to a kwarg-able format.
    """
    # Python 3 only - no need for six compatibility
    return uni_dict
