.. _ref-throttling:

==========
Throttling
==========

Sometimes, the client on the other end may request data too frequently or
you have a business use case that dictates that the client should be limited
to a certain number of requests per hour.

For this, Tastypie includes throttling as a way to limit the number of requests
in a timeframe.

Usage
=====

To specify a throttle, add the ``Throttle`` class to the ``Meta`` class on the
``Resource``::

    from django.contrib.auth.models import User
    from tastypie.resources import ModelResource
    from tastypie.throttle import BaseThrottle
    
    
    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            # Add it here.
            throttle = BaseThrottle(throttle_at=100)


Throttle Options
================

Each of the ``Throttle`` classes accepts the following initialization
arguments:

* ``throttle_at`` - the number of requests at which the user should
  be throttled. Default is 150 requests.
* ``timeframe`` - the length of time (in seconds) in which the user
  make up to the ``throttle_at`` requests. Default is 3600 seconds (
  1 hour).
* ``expiration`` - the length of time to retain the times the user
  has accessed the api in the cache. Default is 604800 (1 week).

Tastypie ships with the following ``Throttle`` classes:

``BaseThrottle``
~~~~~~~~~~~~~~~~

The no-op throttle option, this does no throttling but implements much of the
common logic and serves as an api-compatible plug. Very useful for development.

``CacheThrottle``
~~~~~~~~~~~~~~~~~

This uses just the cache to manage throttling. Fast but prone to cache misses
and/or cache restarts.

``CacheDBThrottle``
~~~~~~~~~~~~~~~~~~~

A write-through option that uses the cache first & foremost, but also writes
through to the database to persist access times. Useful for logging client
accesses & with RAM-only caches.


Implementing Your Own Throttle
==============================

Writing a ``Throttle`` class is not quite as simple as the other components.
There are two important methods, ``should_be_throttled`` & ``accessed``. The
``should_be_throttled`` method dictates whether or not the client should be
throttled. The ``accessed`` method allows for the recording of the hit to the
API.

An example of a subclass might be::

    import random
    from tastypie.throttle import BaseThrottle
    
    
    class RandomThrottle(BaseThrottle):
        def should_be_throttled(self, identifier, **kwargs):
            if random.randint(0, 10) % 2 == 0:
              return True
            
            return False
        
        def accessed(self, identifier, **kwargs):
            pass

This throttle class would pick a random number between 0 & 10. If the number is
even, their request is allowed through; otherwise, their request is throttled &
rejected.
