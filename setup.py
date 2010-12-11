#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='django-tastypie',
    version='0.9.5',
    description='A flexible & capable API layer for Django.',
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='http://github.com/toastdriven/django-tastypie/',
    packages=[
        'tastypie',
        'tastypie.utils',
    ],
    package_data={
        'tastypie': ['templates/tastypie/*'],
    },
    requires=[
        'mimeparse',
        'python_dateutil',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)