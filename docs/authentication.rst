.. _authentication:

==============
Authentication
==============

Authentication is the component needed to verify who a
certain user is and to validate their access to the API.

Authentication answers the question "Who is this person?" This usually involves
requiring credentials, such as an API key or username/password or oAuth tokens.

Usage
=====

Using these classes is simple. Simply provide them (or your own class) as a
``Meta`` option to the ``Resource`` in question. For example::

    from django.contrib.auth.models import User
    from tastypie.authentication import BasicAuthentication
    from tastypie.resources import ModelResource


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            # Add it here.
            authentication = BasicAuthentication()


Authentication Options
======================

Tastypie ships with the following ``Authentication`` classes:

.. warning:

    Tastypie, when used with ``django.contrib.auth.models.User``, will check
    to ensure that the ``User.is_active = True`` by default.

    You can disable this behavior by initializing your ``Authentication`` class
    with ``require_active=False``::

        class UserResource(ModelResource):
            class Meta:
                # ...
                authentication = BasicAuthentication(require_active=False)

    *The behavior changed to active-by-default in v0.9.12.*

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
this purpose, so you'll need to ensure ``tastypie`` is in ``INSTALLED_APPS`` and 
that the model's database tables have been created (e.g. via ``django-admin.py syncdb``).

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
    from django.db.models import signals
    from tastypie.models import create_api_key

    signals.post_save.connect(create_api_key, sender=User)

.. warning::

  If you're using Apache & ``mod_wsgi``, you will need to enable
  ``WSGIPassAuthorization On``, otherwise ``mod_wsgi`` strips out the
  ``Authorization`` header. See `this post`_ for details (even though it
  only mentions Basic auth).

.. note::

   In some cases it may be useful to make the ``ApiKey`` model an `abstract
   base class`_. To enable this, set ``settings.TASTYPIE_ABSTRACT_APIKEY`` to
   ``True``. See `the documentation for this setting`_ for more information.

.. _`this post`: http://www.nerdydork.com/basic-authentication-on-mod_wsgi.html
.. _`abstract base class`: https://docs.djangoproject.com/en/dev/topics/db/models/#abstract-base-classes
.. _`the documentation for this setting`: https://django-tastypie.readthedocs.io/en/latest/settings.html#tastypie-abstract-apikey

``SessionAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~~~

This authentication scheme uses the built-in Django sessions to check if
a user is logged. This is typically useful when used by Javascript on the same
site as the API is hosted on.

It requires that the user has logged in & has an active session. They also must
have a valid CSRF token.


``DigestAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~~~

This authentication scheme uses HTTP Digest Auth to check a user's
credentials. The username is their ``django.contrib.auth.models.User``
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


Implementing Your Own Authentication/Authorization
==================================================

Implementing your own ``Authentication`` classes is a simple
process. ``Authentication`` has two methods to override (one of which is
optional but recommended to be customized)::

    from tastypie.authentication import Authentication


    class SillyAuthentication(Authentication):
        def is_authenticated(self, request, **kwargs):
            if 'daniel' in request.user.username:
              return True

            return False

        # Optional but recommended
        def get_identifier(self, request):
            return request.user.username

Under this scheme, only users with 'daniel' in their username will be allowed
in.
