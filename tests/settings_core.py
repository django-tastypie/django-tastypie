from settings import *
INSTALLED_APPS.append('django.contrib.sessions')
INSTALLED_APPS.append('core')

try:
    import oauth_provider
    INSTALLED_APPS.append('oauth_provider')
except ImportError:
    pass

ROOT_URLCONF = 'core.tests.api_urls'
MEDIA_URL = 'http://localhost:8080/media/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'simple': {
            'level': 'ERROR',
            'class': 'core.utils.SimpleHandler',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['simple'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

