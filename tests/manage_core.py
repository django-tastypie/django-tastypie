#!/usr/bin/env python

import os
import sys

from os.path import abspath, dirname, join
from django.core.management import execute_manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    import settings_core as settings
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings_core.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)

