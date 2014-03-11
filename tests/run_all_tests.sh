#!/bin/bash

PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH

VERSION=`django-admin.py --version`
arrIN=(${VERSION//./ })
major=${arrIN[0]}
minor=${arrIN[1]}

#Don't run customuser tests if django's version is less than 1.5.
if [ $major -lt '2' -a $minor -lt '5' ]; then
  ALL="core basic alphanumeric slashless namespaced related validation gis content_gfk authorization"
else
  ALL="core customuser basic alphanumeric slashless namespaced related validation gis content_gfk authorization"
fi



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
    elif [ $type == 'gis' ]; then
        createdb -T template_postgis tastypie.db
    fi
    
    test_name=$module_name
    if [ -n "$type_remainder" ]; then
        test_name=$test_name.$type_remainder
    fi

    ./manage_$type.py test $test_name
    echo; echo
done
