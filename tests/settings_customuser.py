from settings import *
INSTALLED_APPS.append('customuser')
INSTALLED_APPS.append('django.contrib.auth')

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

AUTH_USER_MODEL = 'auth.CustomUser'
