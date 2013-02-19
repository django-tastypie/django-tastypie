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

The default ``Serializer`` supports the following formats:

* json
* jsonp (Disabled by default)
* xml
* yaml
* html
* plist (see http://explorapp.com/biplist/)

Usage
=====

Using this class is simple. It is the default option on all ``Resource``
classes unless otherwise specified. The following code is a no-op, but
demonstrate how you could use your own serializer::

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

Not everyone wants to install or support all the serialization options. To
that end, you can limit the ones available by passing a ``formats=`` kwarg.
For example, to provide only JSON & binary plist serialization::

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
            serializer = Serializer(formats=['json', 'jsonp', 'xml', 'yaml', 'html', 'plist'])


Implementing Your Own Serializer
================================

There are several different use cases here. We'll cover simple examples of
wanting a tweaked format & adding a different format.

To tweak a format, simply override it's ``to_<format>`` & ``from_<format>``
methods. So adding the server time to all output might look like so::

    import time
    from django.utils import simplejson
    from django.core.serializers import json
    from tastypie.serializers import Serializer

    class CustomJSONSerializer(Serializer):
        def to_json(self, data, options=None):
            options = options or {}

            data = self.to_simple(data, options)

            # Add in the current time.
            data['requested_time'] = time.time()

            return simplejson.dumps(data, cls=json.DjangoJSONEncoder, sort_keys=True)

        def from_json(self, content):
            data = simplejson.loads(content)

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
        formats = ['json', 'jsonp', 'xml', 'yaml', 'html', 'plist', 'csv']
        content_types = {
            'json': 'application/json',
            'jsonp': 'text/javascript',
            'xml': 'application/xml',
            'yaml': 'text/yaml',
            'html': 'text/html',
            'plist': 'application/x-plist',
            'csv': 'text/csv',
        }

        def to_csv(self, data, options=None):
            options = options or {}
            data = self.to_simple(data, options)
            raw_data = StringIO.StringIO()
            # Untested, so this might not work exactly right.
            for item in data:
                writer = csv.DictWriter(raw_data, item.keys(), extrasaction='ignore')
                writer.write(item)
            return raw_data

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
    * html
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

``to_html``
~~~~~~~~~~~

.. method:: Serializer.to_html(self, data, options=None):

Reserved for future usage.

The desire is to provide HTML output of a resource, making an API
available to a browser. This is on the TODO list but not currently
implemented.

``from_html``
~~~~~~~~~~~~~

.. method:: Serializer.from_html(self, content):

Reserved for future usage.

The desire is to handle form-based (maybe Javascript?) input, making an
API available to a browser. This is on the TODO list but not currently
implemented.
