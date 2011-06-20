from settings import *
INSTALLED_APPS.append('core')
INSTALLED_APPS.append('inherited_models')

ROOT_URLCONF = 'inherited_models.api.urls'
