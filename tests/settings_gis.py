from settings import *
INSTALLED_APPS.append('gis')

# TIP: Try running with `sudo -u postgres ./run_all_tests.sh gis`
# We just hardcode postgis here.
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DATABASE_NAME,
    }
}

# Run `spatialite tastypie-spatialite.db "SELECT InitSpatialMetaData();"` before
# trying spatialite on disk.
# "InitSpatiaMetaData ()error:"table spatial_ref_sys already exists" can be ignored.
#DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.spatialite'
#DATABASES['default']['NAME'] = 'tastypie-spatialite.db'

ROOT_URLCONF = 'gis.urls'
