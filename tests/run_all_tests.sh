#!/bin/bash

PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH

# complex
ALL="core basic alphanumeric slashless namespaced related validation gis content_gfk authorization"

if [ $# -eq 0 ]; then
    TYPES=$ALL
elif [ $1 == '-h' ]; then
    echo "Valid arguments are: $ALL"
else
    TYPES=$@
fi

for type in $TYPES; do
    echo "** $type **"

    if [ $type == 'related' ]; then
        django-admin.py test ${type}_resource --settings=settings_$type
        continue
    elif [ $type == 'gis' ]; then
        createdb -T template_postgis tastypie.db
    fi

    django-admin.py test $type --settings=settings_$type
    echo; echo
done
