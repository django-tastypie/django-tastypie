from settings import *  # flake8: noqa
INSTALLED_APPS.append('basic')
INSTALLED_APPS.append('slashless')

ROOT_URLCONF = 'slashless.api.urls'

APPEND_SLASH = False
TASTYPIE_ALLOW_MISSING_SLASH = True
