#!/bin/bash
PYTHONPATH=`pwd`:`pwd`/..:$PYTHONPATH
django-admin.py test core --settings=settings
