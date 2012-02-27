#!/bin/bash
PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH

django-admin.py test core --settings=settings_core && \
django-admin.py test basic --settings=settings_basic && \
#django-admin.py test complex --settings=settings_complex && \
django-admin.py test alphanumeric --settings=settings_alphanumeric && \
django-admin.py test slashless --settings=settings_slashless && \
django-admin.py test namespaced --settings=settings_namespaced && \
django-admin.py test related_resource --settings=settings_related && \
django-admin.py test validation --settings=settings_validation
