from __future__ import unicode_literals
import datetime
import re
import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils.encoding import force_text, smart_bytes
from django.core.serializers import json as djangojson

from tastypie.bundle import Bundle
from tastypie.exceptions import BadRequest, UnsupportedFormat
from tastypie.utils import format_datetime, format_date, format_time, make_naive

try:
    import defusedxml.lxml as lxml
    from defusedxml.common import DefusedXmlException
    from defusedxml.lxml import parse as parse_xml
    from lxml.etree import Element, tostring, LxmlError, XMLParser
except ImportError:
    lxml = None

try:
    import yaml
    from django.core.serializers import pyyaml
except ImportError:
    yaml = None

try:
    import biplist
except ImportError:
    biplist = None

import json


XML_ENCODING = re.compile('<\?xml.*?\?>', re.IGNORECASE)


# Ugh & blah.
# So doing a regular dump is generally fine, since Tastypie doesn't usually
# serialize advanced types. *HOWEVER*, it will dump out Python Unicode strings
# as a custom YAML tag, which of course ``yaml.safe_load`` can't handle.
if yaml is not None:
    from yaml.constructor import SafeConstructor
    from yaml.loader import Reader, Scanner, Parser, Composer, Resolver

    class TastypieConstructor(SafeConstructor):
        def construct_yaml_unicode_dammit(self, node):
            value = self.construct_scalar(node)
            try:
                return value.encode('ascii')
            except UnicodeEncodeError:
                return value

    TastypieConstructor.add_constructor(u'tag:yaml.org,2002:python/unicode', TastypieConstructor.construct_yaml_unicode_dammit)

    class TastypieLoader(Reader, Scanner, Parser, Composer, TastypieConstructor, Resolver):
        def __init__(self, stream):
            Reader.__init__(self, stream)
            Scanner.__init__(self)
            Parser.__init__(self)
            Composer.__init__(self)
            TastypieConstructor.__init__(self)
            Resolver.__init__(self)


class Serializer(object):
    """
    A swappable class for serialization.

    This handles most types of data as well as the following output formats::

        * json
        * jsonp (Disabled by default)
        * xml
        * yaml
        * html
        * plist (see http://explorapp.com/biplist/)

    It was designed to make changing behavior easy, either by overridding the
    various format methods (i.e. ``to_json``), by changing the
    ``formats/content_types`` options or by altering the other hook methods.
    """

    formats = ['json', 'xml', 'yaml', 'html', 'plist']

    content_types = {'json': 'application/json',
                     'jsonp': 'text/javascript',
                     'xml': 'application/xml',
                     'yaml': 'text/yaml',
                     'html': 'text/html',
                     'plist': 'application/x-plist'}

    def __init__(self, formats=None, content_types=None, datetime_formatting=None):
        if datetime_formatting is not None:
            self.datetime_formatting = datetime_formatting
        else:
            self.datetime_formatting = getattr(settings, 'TASTYPIE_DATETIME_FORMATTING', 'iso-8601')

        self.supported_formats = []

        if content_types is not None:
            self.content_types = content_types

        if formats is not None:
            self.formats = formats

        if self.formats is Serializer.formats and hasattr(settings, 'TASTYPIE_DEFAULT_FORMATS'):
            # We want TASTYPIE_DEFAULT_FORMATS to override unmodified defaults but not intentational changes
            # on Serializer subclasses:
            self.formats = settings.TASTYPIE_DEFAULT_FORMATS

        if not isinstance(self.formats, (list, tuple)):
            raise ImproperlyConfigured('Formats should be a list or tuple, not %r' % self.formats)

        for format in self.formats:
            try:
                self.supported_formats.append(self.content_types[format])
            except KeyError:
                raise ImproperlyConfigured("Content type for specified type '%s' not found. Please provide it at either the class level or via the arguments." % format)

    def get_mime_for_format(self, format):
        """
        Given a format, attempts to determine the correct MIME type.

        If not available on the current ``Serializer``, returns
        ``application/json`` by default.
        """
        try:
            return self.content_types[format]
        except KeyError:
            return 'application/json'

    def format_datetime(self, data):
        """
        A hook to control how datetimes are formatted.

        Can be overridden at the ``Serializer`` level (``datetime_formatting``)
        or globally (via ``settings.TASTYPIE_DATETIME_FORMATTING``).

        Default is ``iso-8601``, which looks like "2010-12-16T03:02:14".
        """
        data = make_naive(data)
        if self.datetime_formatting == 'rfc-2822':
            return format_datetime(data)
        if self.datetime_formatting == 'iso-8601-strict':
            # Remove microseconds to strictly adhere to iso-8601
            data = data - datetime.timedelta(microseconds = data.microsecond)

        return data.isoformat()

    def format_date(self, data):
        """
        A hook to control how dates are formatted.

        Can be overridden at the ``Serializer`` level (``datetime_formatting``)
        or globally (via ``settings.TASTYPIE_DATETIME_FORMATTING``).

        Default is ``iso-8601``, which looks like "2010-12-16".
        """
        if self.datetime_formatting == 'rfc-2822':
            return format_date(data)

        return data.isoformat()

    def format_time(self, data):
        """
        A hook to control how times are formatted.

        Can be overridden at the ``Serializer`` level (``datetime_formatting``)
        or globally (via ``settings.TASTYPIE_DATETIME_FORMATTING``).

        Default is ``iso-8601``, which looks like "03:02:14".
        """
        if self.datetime_formatting == 'rfc-2822':
            return format_time(data)
        if self.datetime_formatting == 'iso-8601-strict':
            # Remove microseconds to strictly adhere to iso-8601
            data = (datetime.datetime.combine(datetime.date(1,1,1),data) - datetime.timedelta(microseconds = data.microsecond)).time()

        return data.isoformat()

    def serialize(self, bundle, format='application/json', options=None):
        """
        Given some data and a format, calls the correct method to serialize
        the data and returns the result.
        """
        desired_format = None
        if options is None:
            options = {}

        for short_format, long_format in self.content_types.items():
            if format == long_format:
                if hasattr(self, "to_%s" % short_format):
                    desired_format = short_format
                    break

        if desired_format is None:
            raise UnsupportedFormat("The format indicated '%s' had no available serialization method. Please check your ``formats`` and ``content_types`` on your Serializer." % format)

        serialized = getattr(self, "to_%s" % desired_format)(bundle, options)
        return serialized

    def deserialize(self, content, format='application/json'):
        """
        Given some data and a format, calls the correct method to deserialize
        the data and returns the result.
        """
        desired_format = None

        format = format.split(';')[0]

        for short_format, long_format in self.content_types.items():
            if format == long_format:
                if hasattr(self, "from_%s" % short_format):
                    desired_format = short_format
                    break

        if desired_format is None:
            raise UnsupportedFormat("The format indicated '%s' had no available deserialization method. Please check your ``formats`` and ``content_types`` on your Serializer." % format)

        if isinstance(content, six.binary_type):
            content = force_text(content)

        deserialized = getattr(self, "from_%s" % desired_format)(content)
        return deserialized

    def to_simple(self, data, options):
        """
        For a piece of data, attempts to recognize it and provide a simplified
        form of something complex.

        This brings complex Python data structures down to native types of the
        serialization format(s).
        """
        if isinstance(data, (list, tuple)):
            return [self.to_simple(item, options) for item in data]
        if isinstance(data, dict):
            return dict((key, self.to_simple(val, options)) for (key, val) in data.items())
        elif isinstance(data, Bundle):
            return dict((key, self.to_simple(val, options)) for (key, val) in data.data.items())
        elif hasattr(data, 'dehydrated_type'):
            if getattr(data, 'dehydrated_type', None) == 'related' and data.is_m2m == False:
                if data.full:
                    return self.to_simple(data.fk_resource, options)
                else:
                    return self.to_simple(data.value, options)
            elif getattr(data, 'dehydrated_type', None) == 'related' and data.is_m2m == True:
                if data.full:
                    return [self.to_simple(bundle, options) for bundle in data.m2m_bundles]
                else:
                    return [self.to_simple(val, options) for val in data.value]
            else:
                return self.to_simple(data.value, options)
        elif isinstance(data, datetime.datetime):
            return self.format_datetime(data)
        elif isinstance(data, datetime.date):
            return self.format_date(data)
        elif isinstance(data, datetime.time):
            return self.format_time(data)
        elif isinstance(data, bool):
            return data
        elif isinstance(data, (six.integer_types, float)):
            return data
        elif data is None:
            return None
        else:
            return force_text(data)

    def to_etree(self, data, options=None, name=None, depth=0):
        """
        Given some data, converts that data to an ``etree.Element`` suitable
        for use in the XML output.
        """
        if isinstance(data, (list, tuple)):
            element = Element(name or 'objects')
            if name:
                element = Element(name)
                element.set('type', 'list')
            else:
                element = Element('objects')
            for item in data:
                element.append(self.to_etree(item, options, depth=depth+1))
                element[:] = sorted(element, key=lambda x: x.tag)
        elif isinstance(data, dict):
            if depth == 0:
                element = Element(name or 'response')
            else:
                element = Element(name or 'object')
                element.set('type', 'hash')
            for (key, value) in data.items():
                element.append(self.to_etree(value, options, name=key, depth=depth+1))
                element[:] = sorted(element, key=lambda x: x.tag)
        elif isinstance(data, Bundle):
            element = Element(name or 'object')
            for field_name, field_object in data.data.items():
                element.append(self.to_etree(field_object, options, name=field_name, depth=depth+1))
                element[:] = sorted(element, key=lambda x: x.tag)
        elif hasattr(data, 'dehydrated_type'):
            if getattr(data, 'dehydrated_type', None) == 'related' and data.is_m2m == False:
                if data.full:
                    return self.to_etree(data.fk_resource, options, name, depth+1)
                else:
                    return self.to_etree(data.value, options, name, depth+1)
            elif getattr(data, 'dehydrated_type', None) == 'related' and data.is_m2m == True:
                if data.full:
                    element = Element(name or 'objects')
                    for bundle in data.m2m_bundles:
                        element.append(self.to_etree(bundle, options, bundle.resource_name, depth+1))
                else:
                    element = Element(name or 'objects')
                    for value in data.value:
                        element.append(self.to_etree(value, options, name, depth=depth+1))
            else:
                return self.to_etree(data.value, options, name)
        else:
            element = Element(name or 'value')
            simple_data = self.to_simple(data, options)
            data_type = get_type_string(simple_data)

            if data_type != 'string':
                element.set('type', get_type_string(simple_data))

            if data_type != 'null':
                if isinstance(simple_data, six.text_type):
                    element.text = simple_data
                else:
                    element.text = force_text(simple_data)

        return element

    def from_etree(self, data):
        """
        Not the smartest deserializer on the planet. At the request level,
        it first tries to output the deserialized subelement called "object"
        or "objects" and falls back to deserializing based on hinted types in
        the XML element attribute "type".
        """
        if data.tag == 'request':
            # if "object" or "objects" exists, return deserialized forms.
            elements = data.getchildren()
            for element in elements:
                if element.tag in ('object', 'objects'):
                    return self.from_etree(element)
            return dict((element.tag, self.from_etree(element)) for element in elements)
        elif data.tag == 'object' or data.get('type') == 'hash':
            return dict((element.tag, self.from_etree(element)) for element in data.getchildren())
        elif data.tag == 'objects' or data.get('type') == 'list':
            return [self.from_etree(element) for element in data.getchildren()]
        else:
            type_string = data.get('type')
            if type_string in ('string', None):
                return data.text
            elif type_string == 'integer':
                return int(data.text)
            elif type_string == 'float':
                return float(data.text)
            elif type_string == 'boolean':
                if data.text == 'True':
                    return True
                else:
                    return False
            else:
                return None

    def to_json(self, data, options=None):
        """
        Given some Python data, produces JSON output.
        """
        options = options or {}
        data = self.to_simple(data, options)

        return djangojson.json.dumps(data, cls=djangojson.DjangoJSONEncoder, sort_keys=True, ensure_ascii=False)

    def from_json(self, content):
        """
        Given some JSON data, returns a Python dictionary of the decoded data.
        """
        try:
            return json.loads(content)
        except ValueError:
            raise BadRequest

    def to_jsonp(self, data, options=None):
        """
        Given some Python data, produces JSON output wrapped in the provided
        callback.

        Due to a difference between JSON and Javascript, two
        newline characters, \u2028 and \u2029, need to be escaped.
        See http://timelessrepo.com/json-isnt-a-javascript-subset for
        details.
        """
        options = options or {}
        json = self.to_json(data, options)
        json = json.replace(u'\u2028', u'\\u2028').replace(u'\u2029', u'\\u2029')
        return u'%s(%s)' % (options['callback'], json)

    def to_xml(self, data, options=None):
        """
        Given some Python data, produces XML output.
        """
        options = options or {}

        if lxml is None:
            raise ImproperlyConfigured("Usage of the XML aspects requires lxml and defusedxml.")

        return tostring(self.to_etree(data, options), xml_declaration=True, encoding='utf-8')

    def from_xml(self, content, forbid_dtd=True, forbid_entities=True):
        """
        Given some XML data, returns a Python dictionary of the decoded data.

        By default XML entity declarations and DTDs will raise a BadRequest
        exception content but subclasses may choose to override this if
        necessary.
        """
        if lxml is None:
            raise ImproperlyConfigured("Usage of the XML aspects requires lxml and defusedxml.")

        try:
            # Stripping the encoding declaration. Because lxml.
            # See http://lxml.de/parsing.html, "Python unicode strings".
            content = XML_ENCODING.sub('', content)
            parsed = parse_xml(
                six.StringIO(content),
                forbid_dtd=forbid_dtd,
                forbid_entities=forbid_entities
            )
        except (LxmlError, DefusedXmlException):
            raise BadRequest()

        return self.from_etree(parsed.getroot())

    def to_yaml(self, data, options=None):
        """
        Given some Python data, produces YAML output.
        """
        options = options or {}

        if yaml is None:
            raise ImproperlyConfigured("Usage of the YAML aspects requires yaml.")

        return yaml.dump(self.to_simple(data, options))

    def from_yaml(self, content):
        """
        Given some YAML data, returns a Python dictionary of the decoded data.
        """
        if yaml is None:
            raise ImproperlyConfigured("Usage of the YAML aspects requires yaml.")

        return yaml.load(content, Loader=TastypieLoader)

    def to_plist(self, data, options=None):
        """
        Given some Python data, produces binary plist output.
        """
        options = options or {}

        if biplist is None:
            raise ImproperlyConfigured("Usage of the plist aspects requires biplist.")

        return biplist.writePlistToString(self.to_simple(data, options))

    def from_plist(self, content):
        """
        Given some binary plist data, returns a Python dictionary of the decoded data.
        """
        if biplist is None:
            raise ImproperlyConfigured("Usage of the plist aspects requires biplist.")

        if isinstance(content, six.text_type):
            content = smart_bytes(content)

        return biplist.readPlistFromString(content)

    def to_html(self, data, options=None):
        """
        Reserved for future usage.

        The desire is to provide HTML output of a resource, making an API
        available to a browser. This is on the TODO list but not currently
        implemented.
        """
        options = options or {}
        return 'Sorry, not implemented yet. Please append "?format=json" to your URL.'

    def from_html(self, content):
        """
        Reserved for future usage.

        The desire is to handle form-based (maybe Javascript?) input, making an
        API available to a browser. This is on the TODO list but not currently
        implemented.
        """
        pass

def get_type_string(data):
    """
    Translates a Python data type into a string format.
    """
    data_type = type(data)

    if data_type in six.integer_types:
        return 'integer'
    elif data_type == float:
        return 'float'
    elif data_type == bool:
        return 'boolean'
    elif data_type in (list, tuple):
        return 'list'
    elif data_type == dict:
        return 'hash'
    elif data is None:
        return 'null'
    elif isinstance(data, six.string_types):
        return 'string'
