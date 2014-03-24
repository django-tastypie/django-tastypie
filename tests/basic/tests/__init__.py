from django.conf import settings

if 'DiscoverRunner' not in settings.TEST_RUNNER:
    from basic.tests.test_http import *
    from basic.tests.test_resources import *
    from basic.tests.test_views import *