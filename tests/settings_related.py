from settings import *  # noqa
INSTALLED_APPS.append('core')
INSTALLED_APPS.append('related_resource')

ROOT_URLCONF = 'related_resource.api.urls'
