from __future__ import unicode_literals

from django.conf import settings
from django.utils import six


_trailing_slash = '/?' if getattr(settings, 'TASTYPIE_ALLOW_MISSING_SLASH', False) else '/'


# for backwards compatibility where 3rd parties still call this like a function.
class CallableUnicode(six.text_type):
    def __call__(self):
        return self


trailing_slash = CallableUnicode(_trailing_slash)
