.. _ref-testing:

=======
Testing
=======

Having integrated unit tests that cover your API's behavior is important, as
it helps provide verification that your API code is still valid & working
correctly with the rest of your application.

Tastypie provides some basic facilities that build on top of `Django's testing`_
support, in the form of a specialized ``TestApiClient`` & ``ResourceTestCase``.

.. _`Django's testing`: https://docs.djangoproject.com/en/dev/topics/testing/

The ``ResourceTestCase`` builds on top of Django's ``TestCase``. It provides quite
a few extra assertion methods that are specific to APIs. Under the hood, it
uses the ``TestApiClient`` to perform requests properly.

The ``TestApiClient`` builds on & exposes an interface similar to that of Django's
``Client``. However, under the hood, it hands all the setup needed to construct
a proper request.


Example Usage
=============

The typical use case will primarily consist of subclassing the
``ResourceTestCase`` class & using the built-in assertions to ensure your
API is behaving correctly. For the purposes of this example, we'll assume the
resource in question looks like::

    from tastypie.authentication import BasicAuthentication
    from tastypie.resources import ModelResource
    from entries.models import Entry


    class EntryResource(ModelResource):
        class Meta:
            queryset = Entry.objects.all()
            authentication = BasicAuthentication()


An example usage might look like::

    import datetime
    from django.contrib.auth.models import User
    from tastypie.test import ResourceTestCase
    from entries.models import Entry


    class EntryResourceTest(ResourceTestCase):
        # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
        # documentation for the gory details.
        fixtures = ['test_entries.json']

        def setUp(self):
            super(EntryResourceTest, self).setUp()

            # Create a user.
            self.username = 'daniel'
            self.password = 'pass'
            self.user = User.objects.create_user(self.username, 'daniel@example.com', self.password)

            # Fetch the ``Entry`` object we'll use in testing.
            # Note that we aren't using PKs because they can change depending
            # on what other tests are running.
            self.entry_1 = Entry.objects.get(slug='first-post')

            # We also build a detail URI, since we will be using it all over.
            # DRY, baby. DRY.
            self.detail_url = '/api/v1/entry/{0}/'.format(self.entry_1.pk)

            # The data we'll send on POST requests. Again, because we'll use it
            # frequently (enough).
            self.post_data = {
                'user': '/api/v1/user/{0}/'.format(self.user.pk),
                'title': 'Second Post!',
                'slug': 'second-post',
                'created': '2012-05-01T22:05:12'
            }

        def get_credentials(self):
            return self.create_basic(username=self.username, password=self.password)

        def test_get_list_unauthorzied(self):
            self.assertHttpUnauthorized(self.api_client.get('/api/v1/entries/', format='json'))

        def test_get_list_json(self):
            resp = self.api_client.get('/api/v1/entries/', format='json', authentication=self.get_credentials())
            self.assertValidJSONResponse(resp)

            # Scope out the data for correctness.
            self.assertEqual(len(self.deserialize(resp)['objects']), 12)
            # Here, we're checking an entire structure for the expected data.
            self.assertEqual(self.deserialize(resp)['objects'][0], {
                'pk': str(self.entry_1.pk),
                'user': '/api/v1/user/{0}/'.format(self.user.pk),
                'title': 'First post',
                'slug': 'first-post',
                'created': '2012-05-01T19:13:42',
                'resource_uri': '/api/v1/entry/{0}/'.format(self.entry_1.pk)
            })

        def test_get_list_xml(self):
            self.assertValidXMLResponse(self.api_client.get('/api/v1/entries/', format='xml', authentication=self.get_credentials()))

        def test_get_detail_unauthenticated(self):
            self.assertHttpUnauthorized(self.api_client.get(self.detail_url, format='json'))

        def test_get_detail_json(self):
            resp = self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials())
            self.assertValidJSONResponse(resp)

            # We use ``assertKeys`` here to just verify the keys, not all the data.
            self.assertKeys(self.deserialize(resp), ['created', 'slug', 'title', 'user'])
            self.assertEqual(self.deserialize(resp)['name'], 'First post')

        def test_get_detail_xml(self):
            self.assertValidXMLResponse(self.api_client.get(self.detail_url, format='xml', authentication=self.get_credentials()))

        def test_post_list_unauthenticated(self):
            self.assertHttpUnauthorized(self.api_client.post('/api/v1/entries/', format='json', data=self.post_data))

        def test_post_list(self):
            # Check how many are there first.
            self.assertEqual(Entry.objects.count(), 5)
            self.assertHttpCreated(self.api_client.post('/api/v1/entries/', format='json', data=self.post_data, authentication=self.get_credentials()))
            # Verify a new one has been added.
            self.assertEqual(Entry.objects.count(), 6)

        def test_put_detail_unauthenticated(self):
            self.assertHttpUnauthorized(self.api_client.put(self.detail_url, format='json', data={}))

        def test_put_detail(self):
            # Grab the current data & modify it slightly.
            original_data = self.deserialize(self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials()))
            new_data = original_data.copy()
            new_data['title'] = 'Updated: First Post'
            new_data['created'] = '2012-05-01T20:06:12'

            self.assertEqual(Entry.objects.count(), 5)
            self.assertHttpAccepted(self.api_client.put(self.detail_url, format='json', data=new_data, authentication=self.get_credentials()))
            # Make sure the count hasn't changed & we did an update.
            self.assertEqual(Entry.objects.count(), 5)
            # Check for updated data.
            self.assertEqual(Entry.objects.get(pk=25).title, 'Updated: First Post')
            self.assertEqual(Entry.objects.get(pk=25).slug, 'first-post')
            self.assertEqual(Entry.objects.get(pk=25).created, datetime.datetime(2012, 3, 1, 13, 6, 12))

        def test_delete_detail_unauthenticated(self):
            self.assertHttpUnauthorized(self.api_client.delete(self.detail_url, format='json'))

        def test_delete_detail(self):
            self.assertEqual(Entry.objects.count(), 5)
            self.assertHttpAccepted(self.api_client.delete(self.detail_url, format='json', authentication=self.get_credentials()))
            self.assertEqual(Entry.objects.count(), 4)

Note that this example doesn't cover other cases, such as filtering, ``PUT`` to
a list endpoint, ``DELETE`` to a list endpoint, ``PATCH`` support, etc.


``ResourceTestCase`` API Reference
----------------------------------

The ``ResourceTestCase`` exposes the following methods for use. Most are
enhanced assertions or provide API-specific behaviors.


``get_credentials``
~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.get_credentials(self)

A convenience method for the user as a way to shorten up the
often repetitious calls to create the same authentication.

Raises ``NotImplementedError`` by default.

Usage::

    class MyResourceTestCase(ResourceTestCase):
        def get_credentials(self):
            return self.create_basic('daniel', 'pass')

        # Then the usual tests...

``create_basic``
~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.create_basic(self, username, password)

Creates & returns the HTTP ``Authorization`` header for use with BASIC Auth.

``create_apikey``
~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.create_apikey(self, username, api_key)

Creates & returns the HTTP ``Authorization`` header for use with ``ApiKeyAuthentication``.

``create_digest``
~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.create_digest(self, username, api_key, method, uri)

Creates & returns the HTTP ``Authorization`` header for use with Digest Auth.

``create_oauth``
~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.create_oauth(self, user)

Creates & returns the HTTP ``Authorization`` header for use with Oauth.

``assertHttpOK``
~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpOK(self, resp)

Ensures the response is returning a HTTP 200.

``assertHttpCreated``
~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpCreated(self, resp)

Ensures the response is returning a HTTP 201.

``assertHttpAccepted``
~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpAccepted(self, resp)

Ensures the response is returning either a HTTP 202 or a HTTP 204.

``assertHttpMultipleChoices``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpMultipleChoices(self, resp)

Ensures the response is returning a HTTP 300.

``assertHttpSeeOther``
~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpSeeOther(self, resp)

Ensures the response is returning a HTTP 303.

``assertHttpNotModified``
~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpNotModified(self, resp)

Ensures the response is returning a HTTP 304.

``assertHttpBadRequest``
~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpBadRequest(self, resp)

Ensures the response is returning a HTTP 400.

``assertHttpUnauthorized``
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpUnauthorized(self, resp)

Ensures the response is returning a HTTP 401.

``assertHttpForbidden``
~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpForbidden(self, resp)

Ensures the response is returning a HTTP 403.

``assertHttpNotFound``
~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpNotFound(self, resp)

Ensures the response is returning a HTTP 404.

``assertHttpMethodNotAllowed``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpMethodNotAllowed(self, resp)

Ensures the response is returning a HTTP 405.

``assertHttpConflict``
~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpConflict(self, resp)

Ensures the response is returning a HTTP 409.

``assertHttpGone``
~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpGone(self, resp)

Ensures the response is returning a HTTP 410.

``assertHttpTooManyRequests``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpTooManyRequests(self, resp)

Ensures the response is returning a HTTP 429.

``assertHttpApplicationError``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpApplicationError(self, resp)

Ensures the response is returning a HTTP 500.

``assertHttpNotImplemented``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertHttpNotImplemented(self, resp)

Ensures the response is returning a HTTP 501.

``assertValidJSON``
~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertValidJSON(self, data)

Given the provided ``data`` as a string, ensures that it is valid JSON &
can be loaded properly.

``assertValidXML``
~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertValidXML(self, data)

Given the provided ``data`` as a string, ensures that it is valid XML &
can be loaded properly.

``assertValidYAML``
~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertValidYAML(self, data)

Given the provided ``data`` as a string, ensures that it is valid YAML &
can be loaded properly.

``assertValidPlist``
~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertValidPlist(self, data)

Given the provided ``data`` as a string, ensures that it is valid binary plist &
can be loaded properly.

``assertValidJSONResponse``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertValidJSONResponse(self, resp)

Given a ``HttpResponse`` coming back from using the ``client``, assert that
you get back:

* An HTTP 200
* The correct content-type (``application/json``)
* The content is valid JSON

``assertValidXMLResponse``
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertValidXMLResponse(self, resp)

Given a ``HttpResponse`` coming back from using the ``client``, assert that
you get back:

* An HTTP 200
* The correct content-type (``application/xml``)
* The content is valid XML

``assertValidYAMLResponse``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertValidYAMLResponse(self, resp)

Given a ``HttpResponse`` coming back from using the ``client``, assert that
you get back:

* An HTTP 200
* The correct content-type (``text/yaml``)
* The content is valid YAML

``assertValidPlistResponse``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertValidPlistResponse(self, resp)

Given a ``HttpResponse`` coming back from using the ``client``, assert that
you get back:

* An HTTP 200
* The correct content-type (``application/x-plist``)
* The content is valid binary plist data

``deserialize``
~~~~~~~~~~~~~~~

.. method:: ResourceTestCase.deserialize(self, resp)

Given a ``HttpResponse`` coming back from using the ``client``, this method
checks the ``Content-Type`` header & attempts to deserialize the data based on
that.

It returns a Python datastructure (typically a ``dict``) of the serialized data.

``serialize``
~~~~~~~~~~~~~

.. method:: ResourceTestCase.serialize(self, data, format='application/json')

Given a Python datastructure (typically a ``dict``) & a desired content-type,
this method will return a serialized string of that data.

``assertKeys``
~~~~~~~~~~~~~~

.. method:: ResourceTestCase.assertKeys(self, data, expected)

This method ensures that the keys of the ``data`` match up to the keys of
``expected``.

It covers the (extremely) common case where you want to make sure the keys of
a response match up to what is expected. This is typically less fragile than
testing the full structure, which can be prone to data changes.


``TestApiClient`` API Reference
-------------------------------

The ``TestApiClient`` simulates a HTTP client making calls to the API. It's
important to note that it uses Django's testing infrastructure, so it's not
making actual calls against a webserver.


``__init__``
~~~~~~~~~~~~

.. method:: TestApiClient.__init__(self, serializer=None)

Sets up a fresh ``TestApiClient`` instance.

If you are employing a custom serializer, you can pass the class to the
``serializer=`` kwarg.

``get_content_type``
~~~~~~~~~~~~~~~~~~~~

.. method:: TestApiClient.get_content_type(self, short_format)

Given a short name (such as ``json`` or ``xml``), returns the full content-type
for it (``application/json`` or ``application/xml`` in this case).

``get``
~~~~~~~

.. method:: TestApiClient.get(self, uri, format='json', data=None, authentication=None, **kwargs)

Performs a simulated ``GET`` request to the provided URI.

Optionally accepts a ``data`` kwarg, which in the case of ``GET``, lets you
send along ``GET`` parameters. This is useful when testing filtering or other
things that read off the ``GET`` params. Example::

    from tastypie.test import TestApiClient
    client = TestApiClient()

    response = client.get('/api/v1/entry/1/', data={'format': 'json', 'title__startswith': 'a', 'limit': 20, 'offset': 60})

Optionally accepts an ``authentication`` kwarg, which should be an HTTP header
with the correct authentication data already setup.

All other ``**kwargs`` passed in get passed through to the Django
``TestClient``. See https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client
for details.

``post``
~~~~~~~~

.. method:: TestApiClient.post(self, uri, format='json', data=None, authentication=None, **kwargs)

Performs a simulated ``POST`` request to the provided URI.

Optionally accepts a ``data`` kwarg. **Unlike** ``GET``, in ``POST`` the
``data`` gets serialized & sent as the body instead of becoming part of the URI.
Example::

    from tastypie.test import TestApiClient
    client = TestApiClient()

    response = client.post('/api/v1/entry/', data={
        'created': '2012-05-01T20:02:36',
        'slug': 'another-post',
        'title': 'Another Post',
        'user': '/api/v1/user/1/',
    })

Optionally accepts an ``authentication`` kwarg, which should be an HTTP header
with the correct authentication data already setup.

All other ``**kwargs`` passed in get passed through to the Django
``TestClient``. See https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client
for details.

``put``
~~~~~~~

.. method:: TestApiClient.put(self, uri, format='json', data=None, authentication=None, **kwargs)

Performs a simulated ``PUT`` request to the provided URI.

Optionally accepts a ``data`` kwarg. **Unlike** ``GET``, in ``PUT`` the
``data`` gets serialized & sent as the body instead of becoming part of the URI.
Example::

    from tastypie.test import TestApiClient
    client = TestApiClient()

    response = client.put('/api/v1/entry/1/', data={
        'created': '2012-05-01T20:02:36',
        'slug': 'another-post',
        'title': 'Another Post',
        'user': '/api/v1/user/1/',
    })

Optionally accepts an ``authentication`` kwarg, which should be an HTTP header
with the correct authentication data already setup.

All other ``**kwargs`` passed in get passed through to the Django
``TestClient``. See https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client
for details.

``patch``
~~~~~~~~~

.. method:: TestApiClient.patch(self, uri, format='json', data=None, authentication=None, **kwargs)

Performs a simulated ``PATCH`` request to the provided URI.

Optionally accepts a ``data`` kwarg. **Unlike** ``GET``, in ``PATCH`` the
``data`` gets serialized & sent as the body instead of becoming part of the URI.
Example::

    from tastypie.test import TestApiClient
    client = TestApiClient()

    response = client.patch('/api/v1/entry/1/', data={
        'created': '2012-05-01T20:02:36',
        'slug': 'another-post',
        'title': 'Another Post',
        'user': '/api/v1/user/1/',
    })

Optionally accepts an ``authentication`` kwarg, which should be an HTTP header
with the correct authentication data already setup.

All other ``**kwargs`` passed in get passed through to the Django
``TestClient``. See https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client
for details.

``delete``
~~~~~~~~~~

.. method:: TestApiClient.delete(self, uri, format='json', data=None, authentication=None, **kwargs)

Performs a simulated ``DELETE`` request to the provided URI.

Optionally accepts a ``data`` kwarg, which in the case of ``DELETE``, lets you
send along ``DELETE`` parameters. This is useful when testing filtering or other
things that read off the ``DELETE`` params. Example::

    from tastypie.test import TestApiClient
    client = TestApiClient()

    response = client.delete('/api/v1/entry/1/', data={'format': 'json'})

Optionally accepts an ``authentication`` kwarg, which should be an HTTP header
with the correct authentication data already setup.

All other ``**kwargs`` passed in get passed through to the Django
``TestClient``. See https://docs.djangoproject.com/en/dev/topics/testing/#module-django.test.client
for details.
