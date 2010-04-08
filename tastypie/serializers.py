from django.core.exceptions import ImproperlyConfigured
from django.core.serializers import json
from django.template import loader, Context
from django.utils import simplejson
from django.utils.encoding import force_unicode
from tastypie.exceptions import UnsupportedFormat
from tastypie.representations.simple import Representation
from tastypie.utils import format_datetime
from tastypie.fields import ApiField
from StringIO import StringIO
import datetime
try:
    import lxml
    from lxml.etree import parse as parse_xml
    from lxml.etree import Element
    from django.core.serializers import xml_serializer
    from xml.etree.ElementTree import tostring
except ImportError:
    lxml = None
try:
    import yaml
    from django.core.serializers import pyyaml
except ImportError:
    yaml = None


class Serializer(object):
    formats = ['json', 'jsonp', 'xml', 'yaml', 'html']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'html': 'text/html',
    }
    
    def __init__(self, formats=None, content_types=None):
        self.supported_formats = []
        
        if formats is not None:
            self.formats = formats
        
        if content_types is not None:
            self.content_types = content_types
        
        for format in self.formats:
            try:
                self.supported_formats.append(self.content_types[format])
            except KeyError:
                raise ImproperlyConfigured("Content type for specified type '%s' not found. Please provide it at either the class level or via the arguments." % format)
    
    def get_mime_for_format(self, format):
        try:
            return self.content_types[format]
        except KeyError:
            return 'application/json'
    
    def serialize(self, representation, format='application/json', options={}):
        desired_format = None
        
        for short_format, long_format in self.content_types.items():
            if format == long_format:
                if hasattr(self, "to_%s" % short_format):
                    desired_format = short_format
                    break
        
        if desired_format is None:
            raise UnsupportedFormat("The format indicated '%s' had no available serialization method. Please check your ``formats`` and ``content_types`` on your Serializer." % format)
        
        serialized = getattr(self, "to_%s" % desired_format)(representation, options)
        return serialized
    
    def deserialize(self, content, format='application/json'):
        desired_format = None
        
        for short_format, long_format in self.content_types.items():
            if format == long_format:
                if hasattr(self, "from_%s" % short_format):
                    desired_format = short_format
                    break
        
        if desired_format is None:
            raise UnsupportedFormat("The format indicated '%s' had no available deserialization method. Please check your ``formats`` and ``content_types`` on your Serializer." % format)
        
        deserialized = getattr(self, "from_%s" % desired_format)(content)
        return deserialized

    def to_simple(self, data, options):
        if type(data) in (list, tuple):
            return [self.to_simple(item, options) for item in data]
        elif isinstance(data, dict):
            return dict((key, self.to_simple(val, options)) for (key, val) in data.iteritems())
        elif isinstance(data, Representation):
            object = {}
            for field_name, field_object in data.fields.items():
                object[field_name] = self.to_simple(field_object, options)
            return object
        elif isinstance(data, ApiField):
            return self.to_simple(data.value, options)
        elif isinstance(data, datetime.datetime):
            return format_datetime(data)
        elif isinstance(data, bool):
            return data
        elif type(data) in (long, int):
            return data
        elif data is None:
            return None
        else:
            return force_unicode(data)
    
    def to_etree(self, data, options=None, name=None, depth=0):
        if type(data) in (list, tuple):
            element = Element(name or 'objects')
            for item in data:
                element.append(self.to_etree(item, options, name='object', depth=depth+1))
        elif isinstance(data, dict):
            if depth == 0:
                element = Element(name or 'response')
            else:
                element = Element(name or 'object')
            for (key, value) in data.iteritems():
                element.append(self.to_etree(value, options, name=key, depth=depth+1))
        elif isinstance(data, Representation):
            element = Element('object')
            for field_name, field_object in data.fields.items():
                element.append(self.to_etree(field_object, options, name=field_name, depth=depth+1))
        elif isinstance(data, ApiField):
            element = Element(name)
            element.text = force_unicode(self.to_simple(data, options))
        else:
            element = Element(name or 'value')
            element.text = force_unicode(data)
        return element

    def from_etree(self, data):
        # TODO: write XML etree deserialization
        pass
    
    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder, sort_keys=True)

    def from_json(self, content):
        return simplejson.loads(content)

    def to_jsonp(self, data, options=None):
        options = options or {}
        return '%s(%s)' % (options['callback'], self.to_json(data, options))

    def to_xml(self, data, options=None):
        options = options or {}
        if lxml is None:
            raise ImproperlyConfigured("Usage of the XML aspects requires lxml.")
        return tostring(self.to_etree(data, options))
    
    def from_xml(self, content):
        if lxml is None:
            raise ImproperlyConfigured("Usage of the XML aspects requires lxml.")
        return self.from_etree(parse_xml(StringIO(content)).get_root())
    
    def to_yaml(self, data, options=None):
        options = options or {}
        if yaml is None:
            raise ImproperlyConfigured("Usage of the YAML aspects requires yaml.")
        
        return yaml.dump(data, Dumper=pyyaml.DjangoSafeDumper)
    
    def from_yaml(self, content):
        if yaml is None:
            raise ImproperlyConfigured("Usage of the YAML aspects requires yaml.")
        
        return yaml.load(content)
    
    def to_html(self, data, options=None):
        options = options or {}
        pass
    
    def from_html(self, content):
        pass
