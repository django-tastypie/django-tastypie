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

The HTTP protocol defines a ``Cache-Control`` header, which can be used to tell
clients and intermediaries who is allowed to cache a response and for how long.
Mark Nottingham has a `general caching introduction`_ and the `Django cache
documentation`_ describes how to set caching-related headers in your code. The
range of possible options is beyond the scope of this documentation, but it's
important to know that, by default, Tastypie will prevent responses from being
cached to ensure that clients always receive current information.

.. _general caching introduction: http://www.mnot.net/cache_docs/
.. _Django cache documentation: https://docs.djangoproject.com/en/dev/topics/cache/#controlling-cache-using-other-headers

To override the default ``no-cache`` response, your ``Resource`` should ensure
that your ``cache`` class implements ``cache_control``. The default
``SimpleCache`` does this by default. It uses the timeout passed to the
initialization as the ``max-age`` and ``s-maxage``. By default, it does not
claim to know if the results should be public or privately cached but this can
be changed by passing either a ``public=True`` or a ``private=True`` to the
initialization of the ``SimpleClass``.

Behind the scenes, the return value from the ``cache_control`` method is passed
to the `cache_control`_ helper provided by Django. If you wish to add your own
methods to it, you can do so by overloading the ``cache_control`` method and
modifying the dictionary it returns.::

    from tastypie.cache import SimpleCache

    class NoTransformCache(SimpleCache):

        def cache_control(self):
            control = super(NoTransformCache, self).cache_control()
            control.update({"no_transform": True})
            return control

.. _cache_control: https://docs.djangoproject.com/en/dev/topics/cache/?from=olddocs#controlling-cache-using-other-headers


HTTP Vary
=========

The HTTP protocol defines a ``Vary`` header, which can be used to tell clients
and intermediaries on what headers your response varies. This allows clients to
store a correct response for each type. By default, Tastypie will send the
``Vary: Accept`` header so that a seperate response is cached for each
``Content-Type``. However, if you wish to change this, simply pass a list to
the ``varies`` kwarg of any ``Cache`` class.

It is important to note that if a list is passed, Tastypie not automatically
include the ``Vary: Accept`` and you should include it as a member of your
list.::

    class ExampleResource(Resource):
        class Meta:
            cache = SimpleCache(varies=["Accept", "Cookie"])
