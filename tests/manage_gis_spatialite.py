#!/usr/bin/env python
import os, sys

if __name__ == "__main__":

    # Django 1.8 will run without GEOS so don't run tests if not installed
    try:

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_gis_spatialite")

        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
    except:
        print "GEOS Not installed - not testing gis_spatialite"