from django.conf import settings

if 'DiscoverRunner' not in settings.TEST_RUNNER:
    from alphanumeric.tests.test_views import *
    from alphanumeric.tests.test_http import *
