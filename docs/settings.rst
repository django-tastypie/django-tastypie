.. _ref-settings:

=================
Tastypie Settings
=================

This is a comprehensive list of the settings Tastypie recognizes.


``API_LIMIT_PER_PAGE``
======================

**Optional**

This setting controls the default number of records Tastypie will show
in a list view.

This is only used when a user does not specify a ``limit`` GET parameter and
the ``Resource`` subclass has not overridden the number to be shown.

An example::

    API_LIMIT_PER_PAGE = 50

If you don't want to limit the number of records by default, you can set this setting to 0::

    API_LIMIT_PER_PAGE = 0

Defaults to 20.


``TASTYPIE_FULL_DEBUG``
=======================

**Optional**

This setting controls what the behavior is when an unhandled exception occurs.

If set to ``True`` and ``settings.DEBUG = True``, the standard Django
technical 500 is displayed.

If not set or set to ``False``, Tastypie will return a serialized response.
If ``settings.DEBUG`` is ``True``, you'll get the actual exception message plus
a traceback. If ``settings.DEBUG`` is ``False``, Tastypie will call
``mail_admins()`` and provide a canned error message (which you can override
with ``TASTYPIE_CANNED_ERROR``) in the response.

An example::

    TASTYPIE_FULL_DEBUG = True

Defaults to ``False``.


``TASTYPIE_CANNED_ERROR``
=========================

**Optional**

This setting allows you to override the canned error response when an
unhandled exception is raised and ``settings.DEBUG`` is ``False``.

An example::

    TASTYPIE_CANNED_ERROR = "Oops, we broke it!"

Defaults to ``"Sorry, this request could not be processed. Please try again later."``.


``TASTYPIE_ALLOW_MISSING_SLASH``
================================

**Optional**

This setting allows your URLs to be missing the final slash. Useful for
integrating with other systems.

You must also have ``settings.APPEND_SLASH = False`` so that Django does not
emit HTTP 302 redirects.

An example::

    TASTYPIE_ALLOW_MISSING_SLASH = True

Defaults to ``False``.


``TASTYPIE_DATETIME_FORMATTING``
================================

**Optional**

This setting allows you to globally choose what format your datetime/date/time
data will be formatted in. Valid options are ``iso-8601`` & ``rfc-2822``.

An example::

    TASTYPIE_DATETIME_FORMATTING = 'rfc-2822'

Defaults to ``iso-8601``.
