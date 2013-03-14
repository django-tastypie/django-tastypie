#!/bin/env python

import sys
import subprocess

PYTHONPATH = 'PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}'
ALL = ['core', 'basic', 'alphanumeric', 'slashless', 'namespaced',
       'related_resource', 'validation', 'gis', 'content_gfk', 'authorization']

DJANGO_ADMIN = subprocess.check_output(['which', 'django-admin.py']).strip()
ARGS_STR = 'test {0} --settings=settings_{1}'


def main():
    if len(sys.argv) == 1:
        LABELS = ALL
    elif sys.argv[1] == '-h':
        print("Valid arguments are: %s" % ' '.join(ALL))
        sys.exit(0)
    else:
        LABELS = sys.argv[1:]

    for label in LABELS:
        if '.' in label:
            app = label.split('.')[0]
        else:
            app = label

        if app not in ALL:
            print('')
            print('%s is not a valid app name' % app)
            continue

        print("** %s **" % app)

        if app == 'gis':
            command = 'createdb -T template_postgis tastypie.db'
            subprocess.call(command, shell=True)

        command_args = ARGS_STR.format(label, app)
        command = build_command(command_args)
        print command
        subprocess.call(command, shell=True)

    print('')
    print('')


def build_command(command_args):
    command = ' '.join((PYTHONPATH, DJANGO_ADMIN, command_args))
    return command


if __name__ == '__main__':
    main()
