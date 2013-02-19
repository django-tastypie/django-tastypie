from settings import *

INSTALLED_APPS.append('django.contrib.sites')
INSTALLED_APPS.append('authorization')

ROOT_URLCONF = 'authorization.urls'
