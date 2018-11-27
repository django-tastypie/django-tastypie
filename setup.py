#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


from tastypie import __version__


setup(
    name='django-tastypie',
    version=__version__,
    description='A flexible & capable API layer for Django.',
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='https://github.com/django-tastypie/django-tastypie',
    long_description=open('README.rst', 'r').read(),
    packages=[
        'tastypie',
        'tastypie.utils',
        'tastypie.management',
        'tastypie.management.commands',
        'tastypie.migrations',
        'tastypie.contrib',
        'tastypie.contrib.gis',
        'tastypie.contrib.contenttypes',
    ],
    package_data={
        'tastypie': ['templates/tastypie/*'],
    },
    zip_safe=False,
    requires=[
        'python_mimeparse(>=0.1.4, !=1.5)',
        'dateutil(>=1.5, !=2.0)',
    ],
    install_requires=[
        'python-mimeparse >= 0.1.4, != 1.5',
        'python-dateutil >= 1.5, != 2.0',
    ],
    tests_require=['mock', 'PyYAML', 'lxml', 'defusedxml'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities'
    ],
)
