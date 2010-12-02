from settings import *
INSTALLED_APPS.append('basic')
INSTALLED_APPS.append('slashless')

ROOT_URLCONF = 'slashless.api.urls'

DEBUG = True
APPEND_SLASH = False
TASTYPIE_ALLOW_MISSING_SLASH = True
