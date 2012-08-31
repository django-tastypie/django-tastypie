.. _ref-caching:

=======
Caching
=======

When adding an API to your site, it's important to understand that most
consumers of the API will not be people, but instead machines. This means that
the traditional "fetch-read-click" cycle is no longer measured in minutes but
in seconds or milliseconds.

As such, caching is a very important part of the deployment of your API.
Tastypie ships with two classes to make working with caching easier. These
caches store at the object level, reducing access time on the database.

However, it's worth noting that these do *NOT* cache serialized representations.
For heavy traffic, we'd encourage the use of a caching proxy, especially
Varnish_, as it shines under this kind of usage. It's far faster than Django
views and already neatly handles most situations.

.. _Varnish: http://www.varnish-cache.org/

The first section below demonstrates how to cache at the Django level, reducing
the amount of work required to satisfy a request. In many cases your API serves
web browsers or is behind by a caching proxy such as Varnish_ and it is possible
to set HTTP Cache-Control headers to avoid issuing a request to your application
at all. This is discussed in the :ref:`http-cache-control` section below.

Usage
=====

Using these classes is simple. Simply provide them (or your own class) as a
``Meta`` option to the ``Resource`` in question. For example::

    from django.contrib.auth.models import User
    from tastypie.cache import SimpleCache
    from tastypie.resources import ModelResource


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            # Add it here.
            cache = SimpleCache(timeout=10)


Caching Options
===============

Tastypie ships with the following ``Cache`` classes:

``NoCache``
~~~~~~~~~~~

The no-op cache option, this does no caching but serves as an api-compatible
plug. Very useful for development.

``SimpleCache``
~~~~~~~~~~~~~~~

This option does basic object caching, attempting to find the object in the
cache & writing the object to the cache. It uses Django's current
``CACHE_BACKEND`` to store cached data. The constructor receive a `timeout`
parameter to control per-resource the default timeout for the cache.


Implementing Your Own Cache
===========================

Implementing your own ``Cache`` class is as simple as subclassing ``NoCache``
and overriding the ``get`` & ``set`` methods. For example, a json-backed
cache might look like::

    import json
    from django.conf import settings
    from tastypie.cache import NoCache


    class JSONCache(NoCache):
        def _load(self):
            data_file = open(settings.TASTYPIE_JSON_CACHE, 'r')
            return json.load(data_file)

        def _save(self, data):
            data_file = open(settings.TASTYPIE_JSON_CACHE, 'w')
            return json.dump(data, data_file)

        def get(self, key):
            data = self._load()
            return data.get(key, None)

        def set(self, key, value, timeout=60):
            data = self._load()
            data[key] = value
            self._save(data)

Note that this is *NOT* necessarily an optimal solution, but is simply
demonstrating how one might go about implementing your own ``Cache``.

.. _http-cache-control:

HTTP Cache-Control
==================

The HTTP protocol defines a ``Cache-Control`` header which can be used to tell
clients and intermediaries who is allowed to cache a response and for how long.
Mark Nottingham has a `general caching introduction`_ and the `Django cache
documentation`_ describes how to set caching-related headers in your code. The
range of possible options is beyond the scope of this documentation but it's
important to know that by default tastypie will prevent responses from being
cached to ensure that clients always receive current information.

.. _general caching introduction: http://www.mnot.net/cache_docs/
.. _Django cache documentation:
    https://docs.djangoproject.com/en/dev/topics/cache/#controlling-cache-using-other-headers

To override the default ``no-cache`` response your ``Resource`` should ensure
that ``create_response`` sets a ``Cache-Control`` value on the response, which
causes tastypie not to generate the default header.

One way to do this involves a mixin class::

    from django.utils.cache import patch_cache_control

    class ClientCachedResource(object):
        """Mixin class which sets Cache-Control headers on API responses
           using a ``cache_control`` dictionary from the resource's Meta
           class"""

        def create_response(self, request, data, **response_kwargs):
            response = super(ClientCachedResource, self).create_response(request, data,
                                                                         **response_kwargs)

            if (request.method == "GET" and response.status_code == 200
                and hasattr(self.Meta, "cache_control")):

                cache_control = self.Meta.cache_control.copy()
                patch_cache_control(response, **cache_control)

            return response


This can be added to your resources as desired to allow configurations::

    class RarelyUpdatedResource(ClientCachedResource, Resource):
        class Meta:
            cache_control = {"max_age": 43200, "s_maxage": 7 * 86400}
