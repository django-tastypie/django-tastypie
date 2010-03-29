import datetime
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from tastypie.serializers import Serializer


class SerializerTestCase(TestCase):
    def test_init(self):
        serializer_1 = Serializer()
        self.assertEqual(serializer_1.formats, ['json', 'xml', 'yaml', 'html'])
        self.assertEqual(serializer_1.content_types, {'xml': 'application/xml', 'yaml': 'text/yaml', 'json': 'application/json', 'html': 'text/html'})
        self.assertEqual(serializer_1.supported_formats, ['application/json', 'application/xml', 'text/yaml', 'text/html'])
        
        serializer_2 = Serializer(formats=['json', 'xml'])
        self.assertEqual(serializer_2.formats, ['json', 'xml'])
        self.assertEqual(serializer_2.content_types, {'xml': 'application/xml', 'yaml': 'text/yaml', 'json': 'application/json', 'html': 'text/html'})
        self.assertEqual(serializer_2.supported_formats, ['application/json', 'application/xml'])
        
        serializer_3 = Serializer(formats=['json', 'xml'], content_types={'json': 'text/json', 'xml': 'application/xml'})
        self.assertEqual(serializer_3.formats, ['json', 'xml'])
        self.assertEqual(serializer_3.content_types, {'xml': 'application/xml', 'json': 'text/json'})
        self.assertEqual(serializer_3.supported_formats, ['text/json', 'application/xml'])
        
        self.assertRaises(ImproperlyConfigured, Serializer, formats=['json', 'xml'], content_types={'json': 'text/json'})
    
    def test_to_json(self):
        serializer = Serializer()
        
        sample_1 = {
            'name': 'Daniel',
            'age': 27,
            'date_joined': datetime.date(2010, 3, 27),
        }
        self.assertEqual(serializer.to_json(sample_1), '{"age": 27, "date_joined": "2010-03-27", "name": "Daniel"}')
    
    def test_from_json(self):
        serializer = Serializer()
        
        sample_1 = serializer.from_json('{"age": 27, "date_joined": "2010-03-27", "name": "Daniel"}')
        self.assertEqual(len(sample_1), 3)
        self.assertEqual(sample_1['name'], 'Daniel')
        self.assertEqual(sample_1['age'], 27)
        # FIXME: Not roundtripping appropriately.
        self.assertEqual(sample_1['date_joined'], u'2010-03-27')
