#!/bin/bash
PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH

echo "** Core **"
django-admin.py test core --settings=settings_core

echo
echo
echo "** Basic **"
django-admin.py test basic --settings=settings_basic

#echo
#echo
#echo "** Complex **"
#django-admin.py test complex --settings=settings_complex

echo
echo
echo "** Alphanumeric Primary Keys **"
django-admin.py test alphanumeric --settings=settings_alphanumeric

echo
echo
echo "** Slashless **"
django-admin.py test slashless --settings=settings_slashless

echo
echo
echo "** Namespaced **"
django-admin.py test namespaced --settings=settings_namespaced

echo
echo
echo "** Validation **"
django-admin.py test validation --settings=settings_validation

