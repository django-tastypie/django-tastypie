from django.conf import settings
from django.test.testcases import skipIf

skipIfSpatialite = skipIf('spatialite' in settings.DATABASES['default']['ENGINE'], "Spatialite not supported")

