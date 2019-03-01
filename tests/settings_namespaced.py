from settings import *  # noqa
INSTALLED_APPS.append('basic')
INSTALLED_APPS.append('namespaced')

ROOT_URLCONF = 'namespaced.api.urls'
