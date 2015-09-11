#!/usr/bin/env python
import os, sys
from django.core.exceptions import ImproperlyConfigured

if __name__ == "__main__":

    # Django 1.8 will run without GEOS so don't run tests if not installed
    try:
        from django.contrib.gis.db.models.fields import GeometryField

    except ImproperlyConfigured:
        print "GEOS Not installed - not testing gis_spatialite"

    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_gis_spatialite")

        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)