import os
import versiontools as vt


VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VERSION')


__author__ = 'Daniel Lindsley, Cody Soyland, Matt Croydon, Josh Bohde & Issac Kelly'
__version__ = vt.build_version('your_package_name_here', vt.load_version(VERSION_FILE))
