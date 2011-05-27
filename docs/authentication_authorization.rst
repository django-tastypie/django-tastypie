.. _ref-authentication_authorization:

==============================
Authentication / Authorization
==============================

Authentication & authorization make up the components needed to verify that
a certain user has access to the API and what they can do with it.

Authentication answers the question "can they see this data?" This usually
involves requiring credentials, such as an API key or username/password.

Authorization answers the question "what objects can they modify?" This usually
involves checking permissions, but is open to other implementations.

Usage
=====

Using these classes is simple. Simply provide them (or your own class) as a
``Meta`` option to the ``Resource`` in question. For example::

    from django.contrib.auth.models import User
    from tastypie.authentication import BasicAuthentication
    from tastypie.authorization import DjangoAuthorization
    from tastypie.resources import ModelResource
    
    
    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            # Add it here.
            authentication = BasicAuthentication()
            authorization = DjangoAuthorization()


Authentication Options
======================

Tastypie ships with the following ``Authentication`` classes:

``Authentication``
~~~~~~~~~~~~~~~~~~

The no-op authentication option, the client is always allowed through. Very
useful for development and read-only APIs.

``BasicAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~

This authentication scheme uses HTTP Basic Auth to check a user's credentials.
The username is their ``django.contrib.auth.models.User`` username (assuming
it is present) and their password should also correspond to that entry.

.. warning::

  If you're using Apache & ``mod_wsgi``, you will need to enable
  ``WSGIPassAuthorization On``. See `this post`_ for details.

.. _`this post`: http://www.nerdydork.com/basic-authentication-on-mod_wsgi.html

``ApiKeyAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~~

As an alternative to requiring sensitive data like a password, the
``ApiKeyAuthentication`` allows you to collect just username & a
machine-generated api key. Tastypie ships with a special ``Model`` just for
this purpose, so you'll need to ensure ``tastypie`` is in ``INSTALLED_APPS``.

Tastypie includes a signal function you can use to auto-create ``ApiKey``s.
Hooking it up looks like::

    from django.contrib.auth.models import User
    from django.db import models
    from tastypie.models import create_api_key
    
    models.signals.post_save.connect(create_api_key, sender=User)

``DigestAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~

This authentication scheme uses HTTP Digest Auth to check a user's
credentials.  The username is their ``django.contrib.auth.models.User``
username (assuming it is present) and their password should be their
machine-generated api key. As with ApiKeyAuthentication, ``tastypie``
should be included in ``INSTALLED_APPS``.

.. warning::

  If you're using Apache & ``mod_wsgi``, you will need to enable
  ``WSGIPassAuthorization On``. See `this post`_ for details (even though it
  only mentions Basic auth).

.. _`this post`: http://www.nerdydork.com/basic-authentication-on-mod_wsgi.html

Authorization Options
=====================

Tastypie ships with the following ``Authorization`` classes:

``Authorization``
~~~~~~~~~~~~~~~~~~

The no-op authorization option, no permissions checks are performed.

.. warning::

  This is a potentially dangerous option, as it means *ANY* recognized user
  can modify *ANY* data they encounter in the API. Be careful who you trust.

``ReadOnlyAuthorization``
~~~~~~~~~~~~~~~~~~~~~~~~~

This authorization class only permits reading data, regardless of what the
``Resource`` might think is allowed. This is the default ``Authorization``
class and the safe option.

``DjangoAuthorization``
~~~~~~~~~~~~~~~~~~~~~~~

The most advanced form of authorization, this checks the permission a user
has granted to them (via ``django.contrib.auth.models.Permission``). In
conjunction with the admin, this is a very effective means of control.


Implementing Your Own Authentication/Authorization
==================================================

Implementing your own ``Authentication/Authorization`` classes is a simple
process. ``Authentication`` has two methods to override (one of which is
optional but recommended to be customized) and ``Authorization`` has just one
required method and one optional method::

    from tastypie.authentication import Authentication
    from tastypie.authorization import Authorization
    
    
    class SillyAuthentication(Authentication):
        def is_authenticated(self, request, **kwargs):
            if 'daniel' in request.user.username:
              return True
            
            return False
        
        # Optional but recommended
        def get_identifier(self, request):
            return request.user.username
    
    class SillyAuthorization(Authorization):
        def is_authorized(self, request, object=None):
            if request.user.date_joined.year == 2010:
                return True
            else:
                return False
        
        # Optional but useful for advanced limiting, such as per user.
        def apply_limits(self, request, object_list):
            if request and hasattr(request, 'user'):
                return object_list.filter(author__username=request.user.username)
            
            return object_list.none()

Under this scheme, only users with 'daniel' in their username will be allowed
in, and only those who joined the site in 2010 will be allowed to affect data.

If the optional ``apply_limits`` method is included, each user that fits the
above criteria will only be able to access their own records.
