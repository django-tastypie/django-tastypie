.. _authentication_authorization:

==============================
Authentication / Authorization
==============================

Authentication & authorization make up the components needed to verify who a
certain user is and to validate their access to the API and what they can do
with it.

Authentication answers the question "Who is this person?" This usually involves
requiring credentials, such as an API key or username/password or oAuth tokens.

Authorization answers the question "Is permission granted for this user to take
this action?" This usually involves checking permissions such as
Create/Read/Update/Delete access, or putting limits on what data the user
can access.

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

To use this mechanism, the end user can either specify an ``Authorization``
header or pass the ``username/api_key`` combination as ``GET/POST`` parameters.
Examples::

  # As a header
  # Format is ``Authorization: ApiKey <username>:<api_key>
  Authorization: ApiKey daniel:204db7bcfafb2deb7506b89eb3b9b715b09905c8

  # As GET params
  http://127.0.0.1:8000/api/v1/entries/?username=daniel&api_key=204db7bcfafb2deb7506b89eb3b9b715b09905c8

Tastypie includes a signal function you can use to auto-create ``ApiKey``
objects. Hooking it up looks like::

    from django.contrib.auth.models import User
    from django.db import models
    from tastypie.models import create_api_key

    models.signals.post_save.connect(create_api_key, sender=User)

``DigestAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~~~

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

``OAuthAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~

Handles OAuth, which checks a user's credentials against a separate service.
Currently verifies against OAuth 1.0a services.

This does *NOT* provide OAuth authentication in your API, strictly
consumption.

.. warning::

  If you're used to in-browser OAuth flow (click a "Sign In" button, get
  redirected, login on remote service, get redirected back), this isn't the
  same. Most prominently, expecting that would cause API clients to have to use
  tools like mechanize_ to fill in forms, which would be difficult.

  This authentication expects that you're already followed some sort of OAuth
  flow & that the credentials (Nonce/token/etc) are simply being passed to it.
  It merely checks that the credentials are valid. No requests are made
  to remote services as part of this authentication class.

.. _mechanize: http://pypi.python.org/pypi/mechanize/

``MultiAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~

This authentication class actually wraps any number of other authentication classes,
attempting each until successfully authenticating. For example::

    from django.contrib.auth.models import User
    from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication, MultiAuthentication
    from tastypie.authorization import DjangoAuthorization
    from tastypie.resources import ModelResource

    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']

            authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication())
            authorization = DjangoAuthorization()


In the case of an authentication returning a customized HttpUnauthorized, MultiAuthentication defaults to the first returned one. Authentication schemes that need to control the response, such as the included BasicAuthentication and DigestAuthentication, should be placed first.

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
