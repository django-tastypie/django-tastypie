from settings_gis import *  # noqa

# Run `spatialite tastypie-spatialite.db "SELECT InitSpatialMetaData();"` before
# trying spatialite on disk.
# "InitSpatiaMetaData ()error:"table spatial_ref_sys already exists" can be ignored.
DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.spatialite'
DATABASES['default']['NAME'] = 'tastypie-spatialite.db'


SPATIALITE_LIBRARY_PATH = 'mod_spatialite.so'
