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
            cache = SimpleCache()


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
``CACHE_BACKEND`` to store cached data.


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
