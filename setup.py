#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='django-tastypie',
    version='1.0.0-beta',
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
        'python_dateutil(>=1.5, < 2.0)',
        'python_digest',
    ],
    install_requires=[
        'mimeparse',
        'python_dateutil >= 1.5, < 2.0',
        'python_digest',
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
