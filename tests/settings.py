import os

ADMINS = (
    ('test@example.com', 'Mr. Test'),
)

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

MEDIA_ROOT = os.path.normpath(os.path.join(BASE_PATH, 'media'))

# for django < 1.2
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'tastypie.db'
TEST_DATABASE_NAME = 'tastypie-test.db'

# for django >= 1.2
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tastypie.db',
        'TEST_NAME': 'tastypie-test.db',
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'tastypie',
]

DEBUG = True
TEMPLATE_DEBUG = DEBUG
CACHE_BACKEND = 'locmem://'
