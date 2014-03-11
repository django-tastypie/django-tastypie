from settings import *
INSTALLED_APPS.append('django.contrib.sessions')
INSTALLED_APPS.append('basic')

ROOT_URLCONF = 'basic.urls'

# for some reason the tests for the basic module don't like in-memory sqlite
TEST_DATABASE_NAME = 'tastypie-test.db'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.%s' % DATABASE_ENGINE,
        'NAME': DATABASE_NAME,
        'TEST_NAME': TEST_DATABASE_NAME,
    }
}

