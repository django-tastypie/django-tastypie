dev
===

The current in-progress version. Put your notes here so they can be easily
copied to the release notes for the next release.

Bugfixes
--------

* Change OAuthAuthentication to use storage method to get user. (Closes #657)
* Fixed UnicodeDecodeError in _handle_500(). (Fixes #1190)
* Fix get_via_uri not working for alphabetic ids that contain the resource name (Fixes #1239, Closes #1240)
* Don't enable unsupported formats by default. (Fixes #1451)
* Gave ApiKey a __str__ implementation that works in Python 2 and 3. (Fixes #1459, Closes #1460)
* Improved admin UI for API Keys (Closes #1262)
