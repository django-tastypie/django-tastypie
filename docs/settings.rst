.. _ref-settings:

=================
Tastypie Settings
=================

This is a comprehensive list of the settings Tastypie recognizes.


``API_LIMIT_PER_PAGE``
======================

**Optional**

This setting controls what the default number of records Tastypie will show
in a list view is.

This is only used when a user does not specify a ``limit`` GET parameter and
the ``Resource`` subclass has not overridden the number to be shown.

An example::

    API_LIMIT_PER_PAGE = 50

Defaults to 20.
