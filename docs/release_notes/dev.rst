dev
===

The current in-progress version. Put your notes here so they can be easily
copied to the release notes for the next release.

Major changes
-------------

remove python 2 code, including the six library, and instances of __future__. Also moved to the unittest mock library.

Bugfixes
--------

* Fix related model filtering in `build_filters` and `check_filtering` (Closes #1618)
