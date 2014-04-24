import warnings
warnings.simplefilter('ignore', Warning)

from django.conf import settings

if 'DiscoverRunner' not in settings.TEST_RUNNER:
    from core.tests.test_api import *
    from core.tests.test_authentication import *
    from core.tests.test_authorization import *
    from core.tests.test_cache import *
    from core.tests.test_commands import *
    from core.tests.test_fields import *
    from core.tests.test_http import *
    from core.tests.test_paginator import *
    from core.tests.test_resources import *
    from core.tests.test_serializers import *
    from core.tests.test_throttle import *
    from core.tests.test_utils import *
    from core.tests.test_validation import *
