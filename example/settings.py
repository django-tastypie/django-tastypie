DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'example.db'

INSTALLED_APPS = [
    # Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    
    # Third party
    'tastypie',
    
    # Custom.
    'api',
    'notes',
]

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ROOT_URLCONF = 'urls'
