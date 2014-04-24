#!/bin/bash

PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH

VERSION=`django-admin.py --version`
arrIN=(${VERSION//./ })
major=${arrIN[0]}
minor=${arrIN[1]}

#Don't run customuser tests if django's version is less than 1.5.
if [ $major -lt '2' -a $minor -lt '5' ]; then
  ALL="core basic alphanumeric slashless namespaced related_resource validation gis content_gfk authorization"
else
  ALL="core customuser basic alphanumeric slashless namespaced related_resource validation gis content_gfk authorization"
fi



if [ $# -eq 0 ]; then
    TYPES=$ALL
elif [ $1 == '-h' ]; then
    echo "Valid arguments are: $ALL"
else
    TYPES=$@
fi

for type in $TYPES; do
    echo "** $type **"

    if [ $type == 'gis' ]; then
        createdb -T template_postgis tastypie.db
    fi

    django-admin.py test $type --settings=settings_$type --traceback
    echo; echo
done
