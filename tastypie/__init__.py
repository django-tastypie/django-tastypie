import os
import rose


VERSION_FILE = os.path.join(os.path.dirname(__file__), 'VERSION')


__author__ = 'Daniel Lindsley, Cody Soyland, Matt Croydon, Josh Bohde & Issac Kelly'
__version__ = rose.build_version('tastypie', rose.load_version(VERSION_FILE))
