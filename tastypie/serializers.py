from django.corte.exceptions import ImproperlyConfigured
from django.core.serializers import json, xml_serializer, pyyaml
from django.template import loader, Context


class Serializer(object):
    formats = ['json', 'xml', 'yaml', 'html']
    content_types = {
        'json': 'application/json',
        'xml': 'application/xml',
        'yaml': '',
        'html': 'text/html',
    }
    supported_formats = []
    
    def __init__(self, formats=None, content_types=None):
        if formats is not None:
            self.formats = formats
        
        if content_types is not None:
            self.content_types = content_types
        
        for format in self.formats:
            try:
                self.supported_formats.append(self.content_types[format])
            except KeyError:
                raise ImproperlyConfigured("Content type for specified type '%s' not found. Please provide it at either the class level or via the arguments." % format)
    
    # FIXME:
    #   - Determine how to pass data. On __init__ or per-method? Leaning
    #     toward per-method.
    
    def to_json(self, data):
        pass
    
    def from_json(self, content):
        pass
    
    def to_xml(self, data):
        pass
    
    def from_xml(self, content):
        pass
    
    def to_yaml(self, data):
        pass
    
    def from_yaml(self, content):
        pass
    
    def to_html(self, data):
        pass
    
    def from_html(self, content):
        pass
    