import os

ADMINS = (
    ('test@example.com', 'Mr. Test'),
)

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

MEDIA_ROOT = os.path.normpath(os.path.join(BASE_PATH, 'media'))
STATIC_ROOT = os.path.normpath(os.path.join(BASE_PATH, 'static'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tastypie.db',
        'TEST_NAME': 'tastypie-test.db'
    }
}
# TEST_DATABASE_NAME = 'tastypie-test.db'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'tastypie',
]

DEBUG = True
TEMPLATE_DEBUG = DEBUG

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}
