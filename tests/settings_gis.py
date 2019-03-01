from settings import *  # noqa
INSTALLED_APPS.append('gis')

# We just hardcode postgis here.
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DATABASE_NAME,
    }
}

ROOT_URLCONF = 'gis.urls'
