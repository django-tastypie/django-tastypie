from django.conf import settings

if 'DiscoverRunner' not in settings.TEST_RUNNER:
    from customuser.tests.custom_user import *
