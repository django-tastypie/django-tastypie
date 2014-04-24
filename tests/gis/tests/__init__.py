from django.conf import settings

if 'DiscoverRunner' not in settings.TEST_RUNNER:
    from gis.tests.http import *
    from gis.tests.views import *
