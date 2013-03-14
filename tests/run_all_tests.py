#!/bin/env python

import sys
import subprocess

PYTHONPATH = 'PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}'
ALL = ['core', 'basic', 'alphanumeric', 'slashless', 'namespaced',
       'related', 'validation', 'gis', 'content_gfk', 'authorization']

DJANGO_ADMIN = subprocess.check_output(['which', 'django-admin.py']).strip()
ARGS_STR = 'test {0} --settings=settings_{0}'


def main():
    if len(sys.argv) == 1:
        TYPES = ALL
    elif sys.argv[1] == '-h':
        print("Valid arguments are: %s" % ' '.join(ALL))
        sys.exit(0)
    else:
        TYPES = sys.argv[1:]

    for type in TYPES:
        print("** %s **" % type)

        if type == 'related':

            command_args = 'test {0}_resource --settings=settings_{0}'.format(type)
            command = build_command(command_args)
            subprocess.call(command, shell=True)

            continue
        elif type == 'gis':
            command = 'createdb -T template_postgis tastypie.db'
            subprocess.call(command, shell=True)

        command_args = ARGS_STR.format(type)
        command = build_command(command_args)
        subprocess.call(command, shell=True)

    print('')
    print('')


def build_command(command_args):
    command = ' '.join((PYTHONPATH, DJANGO_ADMIN, command_args))
    return command


if __name__ == '__main__':
    main()
