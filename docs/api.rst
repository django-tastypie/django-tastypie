.. _ref-api:

===
Api
===

In terms of a REST-style architecture, the "api" is a collection of resources.
In Tastypie, the ``Api`` gathers together the ``Resources`` & provides a nice
way to use them as a set. It handles many of the URLconf details for you,
provides a helpful "top-level" view to show what endpoints are available &
some extra URL resolution juice.


Quick Start
===========

A sample api definition might look something like (usually located in a
URLconf)::

    from tastypie.api import Api
    from myapp.api.resources import UserResource, EntryResource

    v1_api = Api(api_name='v1')
    v1_api.register(UserResource())
    v1_api.register(EntryResource())

    # Standard bits...
    urlpatterns = patterns('',
        (r'^api/', include(v1_api.urls)),
    )


``Api`` Methods
===============

Implements a registry to tie together the various resources that make up
an API.

Especially useful for navigation, HATEOAS and for providing multiple
versions of your API.

Optionally supplying ``api_name`` allows you to name the API. Generally,
this is done with version numbers (i.e. ``v1``, ``v2``, etc.) but can
be named any string.

``register``
~~~~~~~~~~~~

.. method:: Api.register(self, resource, canonical=True):

Registers an instance of a ``Resource`` subclass with the API.

Optionally accept a ``canonical`` argument, which indicates that the
resource being registered is the canonical variant. Defaults to
``True``.

``unregister``
~~~~~~~~~~~~~~

.. method:: Api.unregister(self, resource_name):

If present, unregisters a resource from the API.

``canonical_resource_for``
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: Api.canonical_resource_for(self, resource_name):

Returns the canonical resource for a given ``resource_name``.

``override_urls``
-----------------

.. method:: Api.override_urls(self):

Deprecated. Will be removed by v1.0.0. Please use ``Api.prepend_urls`` instead.

``prepend_urls``
----------------

.. method:: Api.prepend_urls(self):

A hook for adding your own URLs or matching before the default URLs. Useful for
adding custom endpoints or overriding the built-in ones.

Should return a list of individual URLconf lines (**NOT** wrapped in
``patterns``).

``urls``
~~~~~~~~

.. method:: Api.urls(self):

*Property*

Provides URLconf details for the ``Api`` and all registered
``Resources`` beneath it.

``top_level``
~~~~~~~~~~~~~

.. method:: Api.top_level(self, request, api_name=None):

A view that returns a serialized list of all resources registers
to the ``Api``. Useful for discovery.

