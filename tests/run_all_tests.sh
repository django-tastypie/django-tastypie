#!/bin/bash

PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH

VERSION=`django-admin.py --version`
arrIN=(${VERSION//./ })
major=${arrIN[0]}
minor=${arrIN[1]}

ALL="core customuser basic alphanumeric slashless namespaced related validation gis gis_spatialite content_gfk authorization"

if [ $# -eq 0 ]; then
    PYTESTPATHS=$ALL
elif [ $1 == '-h' ]; then
    echo "Valid arguments are: $ALL"
else
    PYTESTPATHS=$@
fi

for pytestpath in $PYTESTPATHS; do
    IFS='.' read -r type type_remainder <<< "$pytestpath"
    
    echo "** $type **"
    module_name=$type
    
    if [ $type == 'related' ]; then
        module_name=${module_name}_resource
    elif [ $type == 'gis_spatialite' ]; then
        module_name='gis'
    fi
    
    test_name=$module_name
    if [ -n "$type_remainder" ]; then
        test_name=$test_name.$type_remainder
    fi
    
    if [ $type == 'gis' ]; then
        createdb -T template_postgis tastypie.db
    elif [ $type == 'gis_spatialite' ]; then
        spatialite tastypie-spatialite.db "SELECT InitSpatialMetaData();"
    fi
    
    echo "./manage_$type.py test $test_name.tests --traceback -t $test_name"
    ./manage_$type.py test $test_name.tests --traceback -t $test_name
    echo; echo
done
