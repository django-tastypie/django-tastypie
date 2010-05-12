import datetime
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from tastypie.serializers import Serializer
from tastypie.resources import ModelResource
from core.models import Note


class NoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)


class SerializerTestCase(TestCase):
    def test_init(self):
        serializer_1 = Serializer()
        self.assertEqual(serializer_1.formats, ['json', 'jsonp', 'xml', 'yaml', 'html'])
        self.assertEqual(serializer_1.content_types, {'xml': 'application/xml', 'yaml': 'text/yaml', 'json': 'application/json', 'jsonp': 'text/javascript', 'html': 'text/html'})
        self.assertEqual(serializer_1.supported_formats, ['application/json', 'text/javascript', 'application/xml', 'text/yaml', 'text/html'])
        
        serializer_2 = Serializer(formats=['json', 'xml'])
        self.assertEqual(serializer_2.formats, ['json', 'xml'])
        self.assertEqual(serializer_2.content_types, {'xml': 'application/xml', 'yaml': 'text/yaml', 'json': 'application/json', 'jsonp': 'text/javascript', 'html': 'text/html'})
        self.assertEqual(serializer_2.supported_formats, ['application/json', 'application/xml'])
        
        serializer_3 = Serializer(formats=['json', 'xml'], content_types={'json': 'text/json', 'xml': 'application/xml'})
        self.assertEqual(serializer_3.formats, ['json', 'xml'])
        self.assertEqual(serializer_3.content_types, {'xml': 'application/xml', 'json': 'text/json'})
        self.assertEqual(serializer_3.supported_formats, ['text/json', 'application/xml'])
        
        self.assertRaises(ImproperlyConfigured, Serializer, formats=['json', 'xml'], content_types={'json': 'text/json'})

    def get_sample1(self):
        return {
            'name': 'Daniel',
            'age': 27,
            'date_joined': datetime.date(2010, 3, 27),
        }

    def get_sample2(self):
        return {
            'somelist': ['hello', 1, None],
            'somehash': {'pi': 3.14, 'foo': 'bar'},
            'somestring': 'hello',
            'true': True,
            'false': False,
        }

    def test_to_xml(self):
        serializer = Serializer()
        sample_1 = self.get_sample1()
        self.assertEqual(serializer.to_xml(sample_1), '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><age type="integer">27</age><name>Daniel</name><date_joined>27 Mar 2010</date_joined></response>')

    def test_to_xml2(self):
        serializer = Serializer()
        sample_2 = self.get_sample2()
        self.assertEqual(serializer.to_xml(sample_2), '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><somelist type="list"><value>hello</value><value type="integer">1</value><value type="null"/></somelist><somehash type="hash"><pi type="float">3.14</pi><foo>bar</foo></somehash><false type="boolean">False</false><true type="boolean">True</true><somestring>hello</somestring></response>')

    def test_from_xml(self):
        serializer = Serializer()
        data = '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<request><age type="integer">27</age><name>Daniel</name><date_joined>2010-03-27</date_joined><rocksdahouse type="boolean">True</rocksdahouse></request>'
        self.assertEqual(serializer.from_xml(data), {'rocksdahouse': True, 'age': 27, 'name': 'Daniel', 'date_joined': '2010-03-27'})

    def test_from_xml2(self):
        serializer = Serializer()
        data = '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<request><somelist type="list"><value>hello</value><value type="integer">1</value><value type="null"/></somelist><somehash type="hash"><pi type="float">3.14</pi><foo>bar</foo></somehash><false type="boolean">False</false><true type="boolean">True</true><somestring>hello</somestring></request>'
        self.assertEqual(serializer.from_xml(data), self.get_sample2())
    
    def test_to_json(self):
        serializer = Serializer()
        
        sample_1 = self.get_sample1()
        self.assertEqual(serializer.to_json(sample_1), '{"age": 27, "date_joined": "27 Mar 2010", "name": "Daniel"}')
    
    def test_from_json(self):
        serializer = Serializer()
        
        sample_1 = serializer.from_json('{"age": 27, "date_joined": "2010-03-27", "name": "Daniel"}')
        self.assertEqual(len(sample_1), 3)
        self.assertEqual(sample_1['name'], 'Daniel')
        self.assertEqual(sample_1['age'], 27)
        self.assertEqual(sample_1['date_joined'], u'2010-03-27')

    def test_round_trip_xml(self):
        serializer = Serializer()
        sample_data = self.get_sample2()
        serialized = serializer.to_xml(sample_data)
        # "response" tags need to be changed to "request" to deserialize properly.
        # A string substitution works here.
        serialized = serialized.replace('response', 'request')
        unserialized = serializer.from_xml(serialized)
        self.assertEqual(sample_data, unserialized)

    def test_round_trip_json(self):
        serializer = Serializer()
        sample_data = self.get_sample2()
        serialized = serializer.to_json(sample_data)
        unserialized = serializer.from_json(serialized)
        self.assertEqual(sample_data, unserialized)

    def test_round_trip_yaml(self):
        serializer = Serializer()
        sample_data = self.get_sample2()
        serialized = serializer.to_yaml(sample_data)
        unserialized = serializer.from_yaml(serialized)
        self.assertEqual(sample_data, unserialized)

    def test_to_jsonp(self):
        serializer = Serializer()

        sample_1 = self.get_sample1()
        options = {'callback': 'myCallback'}
        self.assertEqual(serializer.to_jsonp(sample_1, options), 'myCallback({"age": 27, "date_joined": "27 Mar 2010", "name": "Daniel"})')

class ResourceSerializationTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def setUp(self):
        super(ResourceSerializationTestCase, self).setUp()
        self.resource = NoteResource()
        self.obj_list = [self.resource.full_dehydrate(obj=obj) for obj in self.resource.obj_get_list()]

    def test_to_xml_multirepr(self):
        serializer = Serializer()
        self.assertEqual(serializer.to_xml(self.obj_list), '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<objects><object><updated>Tue, 30 Mar 2010 20:05:00 -0500</updated><title>First Post!</title><created>Tue, 30 Mar 2010 20:05:00 -0500</created><is_active type="boolean">True</is_active><content>This is my very first post using my shiny new API. Pretty sweet, huh?</content><slug>first-post</slug><resource_uri></resource_uri></object><object><updated>Wed, 31 Mar 2010 20:05:00 -0500</updated><title>Another Post</title><created>Wed, 31 Mar 2010 20:05:00 -0500</created><is_active type="boolean">True</is_active><content>The dog ate my cat today. He looks seriously uncomfortable.</content><slug>another-post</slug><resource_uri></resource_uri></object><object><updated>Thu, 1 Apr 2010 20:05:00 -0500</updated><title>Recent Volcanic Activity.</title><created>Thu, 1 Apr 2010 20:05:00 -0500</created><is_active type="boolean">True</is_active><content>My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.</content><slug>recent-volcanic-activity</slug><resource_uri></resource_uri></object><object><updated>Fri, 2 Apr 2010 10:05:00 -0500</updated><title>Granny\'s Gone</title><created>Fri, 2 Apr 2010 10:05:00 -0500</created><is_active type="boolean">True</is_active><content>Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!</content><slug>grannys-gone</slug><resource_uri></resource_uri></object></objects>')

    def test_to_xml_single(self):
        serializer = Serializer()
        resource = self.obj_list[0]
        self.assertEqual(serializer.to_xml(resource), '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<object><updated>Tue, 30 Mar 2010 20:05:00 -0500</updated><title>First Post!</title><created>Tue, 30 Mar 2010 20:05:00 -0500</created><is_active type="boolean">True</is_active><content>This is my very first post using my shiny new API. Pretty sweet, huh?</content><slug>first-post</slug><resource_uri></resource_uri></object>')

    def test_to_xml_nested(self):
        serializer = Serializer()
        resource = self.obj_list[0]
        data = {
            'stuff': {
                'foo': 'bar',
                'object': resource,
            }
        }
        self.assertEqual(serializer.to_xml(data), '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><stuff type="hash"><foo>bar</foo><object><updated>Tue, 30 Mar 2010 20:05:00 -0500</updated><title>First Post!</title><created>Tue, 30 Mar 2010 20:05:00 -0500</created><is_active type="boolean">True</is_active><content>This is my very first post using my shiny new API. Pretty sweet, huh?</content><slug>first-post</slug><resource_uri></resource_uri></object></stuff></response>')

    def test_to_json_multirepr(self):
        serializer = Serializer()
        self.assertEqual(serializer.to_json(self.obj_list), '[{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "Thu, 1 Apr 2010 20:05:00 -0500", "is_active": true, "resource_uri": "", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "Thu, 1 Apr 2010 20:05:00 -0500"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "Fri, 2 Apr 2010 10:05:00 -0500", "is_active": true, "resource_uri": "", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "Fri, 2 Apr 2010 10:05:00 -0500"}]')

    def test_to_json_single(self):
        serializer = Serializer()
        resource = self.obj_list[0]
        self.assertEqual(serializer.to_json(resource), '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}')

    def test_to_json_nested(self):
        serializer = Serializer()
        resource = self.obj_list[0]
        data = {
            'stuff': {
                'foo': 'bar',
                'object': resource,
            }
        }
        self.assertEqual(serializer.to_json(data), '{"stuff": {"foo": "bar", "object": {"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}}}')
