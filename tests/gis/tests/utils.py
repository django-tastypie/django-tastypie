from unittest import skipIf
from django.conf import settings

skipIfSpatialite = skipIf('spatialite' in settings.DATABASES['default']['ENGINE'], "Spatialite not supported")
