import warnings
warnings.simplefilter('ignore', Warning)

from django.conf import settings

if 'DiscoverRunner' not in settings.TEST_RUNNER:
    from content_gfk.tests.test_fields import *
    from content_gfk.tests.test_resources import *
