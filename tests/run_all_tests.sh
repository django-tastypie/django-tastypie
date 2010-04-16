#!/bin/bash
PYTHONPATH=`pwd`:`pwd`/..:$PYTHONPATH
django-admin.py test core --settings=settings_core
django-admin.py test basic --settings=settings_basic
