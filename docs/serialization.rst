.. _ref-serialization:

=============
Serialization
=============

Serialization can be one of the most contentious areas of an API. Everyone
has their own requirements, their own preferred output format & the desire to
have control over what is returned.

As a result, Tastypie ships with a serializer that tries to meet the basic
needs of most use cases, and the flexibility to go outside of that when you
need to.

Usage
=====

Using this class is simple. It is the default option on all ``Resource``
classes unless otherwise specified. The following code is identical to the
defaults but demonstrate how you could use your own serializer::

    from django.contrib.auth.models import User
    from tastypie.resources import ModelResource
    from tastypie.serializers import Serializer


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            # Add it here.
            serializer = Serializer()

Configuring Allowed Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default ``Serializer`` supports the following formats:

* json
* jsonp (Disabled by default)
* xml
* yaml
* plist (see https://bitbucket.org/wooster/biplist)

Not everyone wants to install or support all the serialization options. If you
would like to customize the list of supported formats for your entire site
the :ref:`TASTYPIE_DEFAULT_FORMATS setting <settings.TASTYPIE_DEFAULT_FORMATS>`
allows you to set the default format list site-wide.

If you wish to change the format list for a specific resource, you can pass the
list of supported formats using the ``formats=`` kwarg. For example, to provide
only JSON & binary plist serialization::

    from django.contrib.auth.models import User
    from tastypie.resources import ModelResource
    from tastypie.serializers import Serializer


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            serializer = Serializer(formats=['json', 'plist'])

Enabling the built-in (but disabled by default) JSONP support looks like::

    from django.contrib.auth.models import User
    from tastypie.resources import ModelResource
    from tastypie.serializers import Serializer


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            serializer = Serializer(formats=['json', 'jsonp', 'xml', 'yaml', 'plist'])


Serialization Security
======================

Deserialization of input from unknown or untrusted sources is an intrinsically
risky endeavor and vulnerabilities are regularly found in popular format
libraries. Tastypie adopts and recommends the following approach:

* Support the minimum required set of formats in your application.
  If you do not require a format, it's much safer to disable it
  completely. See :ref:`TASTYPIE_DEFAULT_FORMATS setting <settings.TASTYPIE_DEFAULT_FORMATS>`.
* Some parsers offer additional safety check for use with untrusted content.
  The standard Tastypie Serializer attempts to be secure by default using
  features like PyYAML's
  `safe_load <http://pyyaml.org/wiki/PyYAMLDocumentation#LoadingYAML>`_ function
  and the defusedxml_ security wrapper for popular Python XML libraries.

  .. note::

      Tastypie's precautions only apply to the default :class:`Serializer`. If
      you have written your own serializer subclass we strongly recommend that
      you review your code to ensure that it uses the same precautions.

      If backwards compatibility forces you to load files which require risky
      features we strongly recommend enabling those features only for the
      necessary resources and making your authorization checks as strict as
      possible. The :doc:`authentication` and :doc:`authorization` checks happen
      before deserialization so, for example, a resource which only allowed
      POST or PUT requests to be made by administrators is far less exposed than
      a general API open to the unauthenticated internet.

.. _defusedxml: https://pypi.python.org/pypi/defusedxml


Implementing Your Own Serializer
================================

There are several different use cases here. We'll cover simple examples of
wanting a tweaked format & adding a different format.

To tweak a format, simply override it's ``to_<format>`` & ``from_<format>``
methods. So adding the server time to all output might look like so::

    import time
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    from tastypie.serializers import Serializer

    class CustomJSONSerializer(Serializer):
        def to_json(self, data, options=None):
            options = options or {}

            data = self.to_simple(data, options)

            # Add in the current time.
            data['requested_time'] = time.time()

            return json.dumps(data, cls=DjangoJSONEncoder, sort_keys=True)

        def from_json(self, content):
            data = json.loads(content)

            if 'requested_time' in data:
                # Log the request here...
                pass

            return data

In the case of adding a different format, let's say you want to add a CSV
output option to the existing set. Your ``Serializer`` subclass might look
like::

    import csv
    import StringIO
    from tastypie.serializers import Serializer


    class CSVSerializer(Serializer):
        formats = Serializer.formats + ['csv']

        content_types = dict(
            Serializer.content_types.items() +
            [('csv', 'text/csv')])

        def to_csv(self, data, options=None):
            options = options or {}
            data = self.to_simple(data, options)
            raw_data = StringIO.StringIO()
            if data['objects']:
                fields = data['objects'][0].keys()
                writer = csv.DictWriter(raw_data, fields,
                                        dialect="excel",
                                        extrasaction='ignore')
                header = dict(zip(fields, fields))
                writer.writerow(header)  # In Python 2.7: `writer.writeheader()`
                for item in data['objects']:
                    writer.writerow(item)

            return raw_data.getvalue()

        def from_csv(self, content):
            raw_data = StringIO.StringIO(content)
            data = []
            # Untested, so this might not work exactly right.
            for item in csv.DictReader(raw_data):
                data.append(item)
            return data


``Serializer`` Methods
======================

A swappable class for serialization.

This handles most types of data as well as the following output formats::

    * json
    * jsonp
    * xml
    * yaml
    * plist

It was designed to make changing behavior easy, either by overridding the
various format methods (i.e. ``to_json``), by changing the
``formats/content_types`` options or by altering the other hook methods.

``get_mime_for_format``
~~~~~~~~~~~~~~~~~~~~~~~

.. method:: Serializer.get_mime_for_format(self, format):

Given a format, attempts to determine the correct MIME type.

If not available on the current ``Serializer``, returns
``application/json`` by default.

``format_datetime``
~~~~~~~~~~~~~~~~~~~

.. method:: Serializer.format_datetime(data):

A hook to control how datetimes are formatted.

Can be overridden at the ``Serializer`` level (``datetime_formatting``)
or globally (via ``settings.TASTYPIE_DATETIME_FORMATTING``).

Default is ``iso-8601``, which looks like "2010-12-16T03:02:14".

``format_date``
~~~~~~~~~~~~~~~

.. method:: Serializer.format_date(data):

A hook to control how dates are formatted.

Can be overridden at the ``Serializer`` level (``datetime_formatting``)
or globally (via ``settings.TASTYPIE_DATETIME_FORMATTING``).

Default is ``iso-8601``, which looks like "2010-12-16".

``format_time``
~~~~~~~~~~~~~~~

.. method:: Serializer.format_time(data):

A hook to control how times are formatted.

Can be overridden at the ``Serializer`` level (``datetime_formatting``)
or globally (via ``settings.TASTYPIE_DATETIME_FORMATTING``).

Default is ``iso-8601``, which looks like "03:02:14".

``serialize``
~~~~~~~~~~~~~

.. method:: Serializer.serialize(self, bundle, format='application/json', options={}):

Given some data and a format, calls the correct method to serialize
the data and returns the result.

``deserialize``
~~~~~~~~~~~~~~~

.. method:: Serializer.deserialize(self, content, format='application/json'):

Given some data and a format, calls the correct method to deserialize
the data and returns the result.

``to_simple``
~~~~~~~~~~~~~

.. method:: Serializer.to_simple(self, data, options):

For a piece of data, attempts to recognize it and provide a simplified
form of something complex.

This brings complex Python data structures down to native types of the
serialization format(s).

``to_etree``
~~~~~~~~~~~~

.. method:: Serializer.to_etree(self, data, options=None, name=None, depth=0):

Given some data, converts that data to an ``etree.Element`` suitable
for use in the XML output.

``from_etree``
~~~~~~~~~~~~~~

.. method:: Serializer.from_etree(self, data):

Not the smartest deserializer on the planet. At the request level,
it first tries to output the deserialized subelement called "object"
or "objects" and falls back to deserializing based on hinted types in
the XML element attribute "type".

``to_json``
~~~~~~~~~~~

.. method:: Serializer.to_json(self, data, options=None):

Given some Python data, produces JSON output.

``from_json``
~~~~~~~~~~~~~

.. method:: Serializer.from_json(self, content):

Given some JSON data, returns a Python dictionary of the decoded data.

``to_jsonp``
~~~~~~~~~~~~

.. method:: Serializer.to_jsonp(self, data, options=None):

Given some Python data, produces JSON output wrapped in the provided
callback.

``to_xml``
~~~~~~~~~~

.. method:: Serializer.to_xml(self, data, options=None):

Given some Python data, produces XML output.

``from_xml``
~~~~~~~~~~~~

.. method:: Serializer.from_xml(self, content):

Given some XML data, returns a Python dictionary of the decoded data.

``to_yaml``
~~~~~~~~~~~

.. method:: Serializer.to_yaml(self, data, options=None):

Given some Python data, produces YAML output.

``from_yaml``
~~~~~~~~~~~~~

.. method:: Serializer.from_yaml(self, content):

Given some YAML data, returns a Python dictionary of the decoded data.

``to_plist``
~~~~~~~~~~~~

.. method:: Serializer.to_plist(self, data, options=None):

Given some Python data, produces binary plist output.

``from_plist``
~~~~~~~~~~~~~~

.. method:: Serializer.from_plist(self, content):

Given some binary plist data, returns a Python dictionary of the decoded data.

