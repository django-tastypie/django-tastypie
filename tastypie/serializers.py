from django.core.exceptions import ImproperlyConfigured
from django.core.serializers import json
from django.template import loader, Context
from django.utils import simplejson
from tastypie.exceptions import UnsupportedFormat
try:
    import lxml
    from django.core.serializers import xml_serializer
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
    
    def to_json(self, data, options={}):
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder, sort_keys=True)

    def to_jsonp(self, data, options={}):
        return '%s(%s)' % (options['callback'], self.to_json(data, options))
    
    def from_json(self, content):
        return simplejson.loads(content)
    
    def to_xml(self, data, options={}):
        if lxml is None:
            raise ImproperlyConfigured("Usage of the XML aspects requires lxml.")
        
        # FIXME: This is incomplete and will likely be painful.
    
    def from_xml(self, content):
        if lxml is None:
            raise ImproperlyConfigured("Usage of the XML aspects requires lxml.")
        
        # FIXME: This is incomplete and will likely be painful.
    
    def to_yaml(self, data, options={}):
        if yaml is None:
            raise ImproperlyConfigured("Usage of the YAML aspects requires yaml.")
        
        return yaml.dump(data, Dumper=pyyaml.DjangoSafeDumper)
    
    def from_yaml(self, content):
        if yaml is None:
            raise ImproperlyConfigured("Usage of the YAML aspects requires yaml.")
        
        return yaml.load(content)
    
    def to_html(self, data, options={}):
        pass
    
    def from_html(self, content):
        pass
    