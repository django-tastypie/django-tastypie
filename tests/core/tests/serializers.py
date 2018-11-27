# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
import mock
from unittest import skipIf
import yaml

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from tastypie.bundle import Bundle
from tastypie import fields
from tastypie.exceptions import BadRequest
from tastypie.serializers import _get_default_formats, Serializer
from tastypie.resources import ModelResource

from core.models import Note

try:
    import biplist
except ImportError:
    biplist = None


skipIfNoBiplist = skipIf(biplist is None, 'biplist not present')


class UnsafeObject(object):
    pass


class NoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)


class AnotherNoteResource(ModelResource):
    aliases = fields.ListField(attribute='aliases', null=True)
    meta = fields.DictField(attribute='metadata', null=True)
    owed = fields.DecimalField(attribute='money_owed', null=True)

    class Meta:
        resource_name = 'anothernotes'
        queryset = Note.objects.filter(is_active=True)

    def dehydrate(self, bundle):
        bundle.data['aliases'] = ['Mr. Smith', 'John Doe']
        bundle.data['meta'] = {'threat': 'high'}
        bundle.data['owed'] = Decimal('102.57')
        return bundle


class GetDefaultFormatsTestCase(TestCase):
    @mock.patch.multiple('tastypie.serializers', lxml=True, yaml=True, biplist=True)
    def test_all(self):
        formats = _get_default_formats()

        self.assertEqual(formats, ['json', 'xml', 'yaml', 'plist'])

    @mock.patch.multiple('tastypie.serializers', lxml=False, yaml=False, biplist=False)
    def test_json_only(self):
        formats = _get_default_formats()

        self.assertEqual(formats, ['json'])


class SerializerTestCase(TestCase):
    def test_init(self):
        serializer_1 = Serializer()
        self.assertEqual(serializer_1.formats, ['json', 'xml', 'yaml', 'plist'])
        self.assertEqual(serializer_1.content_types, {'xml': 'application/xml', 'yaml': 'text/yaml', 'json': 'application/json', 'jsonp': 'text/javascript', 'plist': 'application/x-plist'})
        self.assertEqual(serializer_1.supported_formats, ['application/json', 'application/xml', 'text/yaml', 'application/x-plist'])

        serializer_2 = Serializer(formats=['json', 'xml'])
        self.assertEqual(serializer_2.formats, ['json', 'xml'])
        self.assertEqual(serializer_2.content_types, {'xml': 'application/xml', 'yaml': 'text/yaml', 'json': 'application/json', 'jsonp': 'text/javascript', 'plist': 'application/x-plist'})
        self.assertEqual(serializer_2.supported_formats, ['application/json', 'application/xml'])

        serializer_3 = Serializer(formats=['json', 'xml'], content_types={'json': 'text/json', 'xml': 'application/xml'})
        self.assertEqual(serializer_3.formats, ['json', 'xml'])
        self.assertEqual(serializer_3.content_types, {'xml': 'application/xml', 'json': 'text/json'})
        self.assertEqual(serializer_3.supported_formats, ['text/json', 'application/xml'])

        serializer_4 = Serializer(formats=['plist', 'json'], content_types={'plist': 'application/x-plist', 'json': 'application/json'})
        self.assertEqual(serializer_4.formats, ['plist', 'json'])
        self.assertEqual(serializer_4.content_types, {'plist': 'application/x-plist', 'json': 'application/json'})
        self.assertEqual(serializer_4.supported_formats, ['application/x-plist', 'application/json'])

        self.assertRaises(ImproperlyConfigured, Serializer, formats=['json', 'xml'], content_types={'json': 'text/json'})

    def test_default_formats_setting(self):
        with self.settings(TASTYPIE_DEFAULT_FORMATS=('json', 'xml')):
            # Confirm that the setting will override the default values:
            s = Serializer()
            self.assertEqual(list(s.formats), ['json', 'xml'])
            self.assertEqual(list(s.supported_formats), ['application/json', 'application/xml'])
            self.assertEqual(s.content_types, {'xml': 'application/xml', 'yaml': 'text/yaml', 'json': 'application/json', 'jsonp': 'text/javascript', 'plist': 'application/x-plist'})

            # Confirm that subclasses which set their own formats list won't be overriden:
            class JSONSerializer(Serializer):
                formats = ['json']

            js = JSONSerializer()
            self.assertEqual(list(js.formats), ['json'])
            self.assertEqual(list(js.supported_formats), ['application/json'])

    def get_sample1(self):
        return {
            'name': 'Daniel',
            'age': 27,
            'date_joined': datetime.date(2010, 3, 27),
            'snowman': u'☃',
        }

    def get_sample2(self):
        return {
            'somelist': ['hello', 1, None],
            'somehash': {'pi': 3.14, 'foo': 'bar'},
            'somestring': 'hello',
            'true': True,
            'false': False,
        }

    def test__to_simple__none(self):
        serializer = Serializer()
        val = None
        self.assertIs(serializer.to_simple(val, None), val)

    def test__to_simple__float(self):
        serializer = Serializer()
        val = 1.0
        self.assertIs(serializer.to_simple(val, None), val)

    def test__to_simple__int(self):
        serializer = Serializer()
        val = 1
        self.assertIs(serializer.to_simple(val, None), val)

    def test__to_simple__bool(self):
        serializer = Serializer()
        val = True
        self.assertIs(serializer.to_simple(val, None), val)

    def test__to_simple__dict(self):
        serializer = Serializer()
        val = {'foo': True}
        self.assertEqual(serializer.to_simple(val, None), {'foo': True})

    def test__to_simple__list(self):
        serializer = Serializer()
        val = [True]
        self.assertEqual(serializer.to_simple(val, None), [True])

    def test__to_simple__tuple(self):
        serializer = Serializer()
        val = (True,)
        self.assertEqual(serializer.to_simple(val, None), [True])

    def test__to_simple__bundle(self):
        serializer = Serializer()
        val = Bundle(data={'foo': True})
        self.assertEqual(serializer.to_simple(val, None), {'foo': True})

    def test__to_simple__string(self):
        serializer = Serializer()
        val = b"\xc3\xa1hhh! I'm letting all the \xc3\xa1's out of my body."
        self.assertEqual(serializer.to_simple(val, None), u"áhhh! I'm letting all the á's out of my body.")

    def test__to_simple__datetime(self):
        serializer = Serializer()
        self.assertEqual(serializer.to_simple(datetime.datetime(2010, 12, 16, 2, 31, 33), None), '2010-12-16T02:31:33')

    def test__to_simple__date(self):
        serializer = Serializer()
        self.assertEqual(serializer.to_simple(datetime.date(2010, 12, 16), None), '2010-12-16')

    def test__to_simple__time(self):
        serializer = Serializer()
        self.assertEqual(serializer.to_simple(datetime.time(2, 31, 33), None), '02:31:33')

    def test_format_datetime(self):
        serializer = Serializer()
        self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33)), '2010-12-16T02:31:33')

        serializer = Serializer(datetime_formatting='iso-8601')
        self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33)), '2010-12-16T02:31:33')

        serializer = Serializer(datetime_formatting='iso-8601-strict')
        self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33, 10)), '2010-12-16T02:31:33')

        serializer = Serializer(datetime_formatting='rfc-2822')
        self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33)), u'Thu, 16 Dec 2010 02:31:33 -0600')

        serializer = Serializer(datetime_formatting='random-garbage')
        self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33)), '2010-12-16T02:31:33')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='iso-8601'):
            serializer = Serializer()
            self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33)), '2010-12-16T02:31:33')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='iso-8601-strict'):
            serializer = Serializer()
            self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33, 10)), '2010-12-16T02:31:33')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='rfc-2822'):
            serializer = Serializer()
            self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33)), u'Thu, 16 Dec 2010 02:31:33 -0600')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='random-garbage'):
            serializer = Serializer()
            self.assertEqual(serializer.format_datetime(datetime.datetime(2010, 12, 16, 2, 31, 33)), '2010-12-16T02:31:33')

    def test_format_date(self):
        serializer = Serializer()
        self.assertEqual(serializer.format_date(datetime.date(2010, 12, 16)), '2010-12-16')

        serializer = Serializer(datetime_formatting='iso-8601')
        self.assertEqual(serializer.format_date(datetime.date(2010, 12, 16)), '2010-12-16')

        serializer = Serializer(datetime_formatting='rfc-2822')
        self.assertEqual(serializer.format_date(datetime.date(2010, 12, 16)), u'16 Dec 2010')

        serializer = Serializer(datetime_formatting='random-garbage')
        self.assertEqual(serializer.format_date(datetime.date(2010, 12, 16)), '2010-12-16')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='iso-8601'):
            serializer = Serializer()
            self.assertEqual(serializer.format_date(datetime.date(2010, 12, 16)), '2010-12-16')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='rfc-2822'):
            serializer = Serializer()
            self.assertEqual(serializer.format_date(datetime.date(2010, 12, 16)), u'16 Dec 2010')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='random-garbage'):
            serializer = Serializer()
            self.assertEqual(serializer.format_date(datetime.date(2010, 12, 16)), '2010-12-16')

    def test_format_time(self):
        serializer = Serializer()
        self.assertEqual(serializer.format_time(datetime.time(2, 31, 33)), '02:31:33')

        serializer = Serializer(datetime_formatting='iso-8601')
        self.assertEqual(serializer.format_time(datetime.time(2, 31, 33)), '02:31:33')

        serializer = Serializer(datetime_formatting='iso-8601-strict')
        self.assertEqual(serializer.format_time(datetime.time(2, 31, 33, 10)), '02:31:33')

        serializer = Serializer(datetime_formatting='rfc-2822')
        self.assertEqual(serializer.format_time(datetime.time(2, 31, 33)), u'02:31:33 -0600')

        serializer = Serializer(datetime_formatting='random-garbage')
        self.assertEqual(serializer.format_time(datetime.time(2, 31, 33)), '02:31:33')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='iso-8601'):
            serializer = Serializer()
            self.assertEqual(serializer.format_time(datetime.time(2, 31, 33)), '02:31:33')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='iso-8601-strict'):
            serializer = Serializer()
            self.assertEqual(serializer.format_time(datetime.time(2, 31, 33, 10)), '02:31:33')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='rfc-2822'):
            serializer = Serializer()
            self.assertEqual(serializer.format_time(datetime.time(2, 31, 33)), u'02:31:33 -0600')

        with self.settings(TASTYPIE_DATETIME_FORMATTING='random-garbage'):
            serializer = Serializer()
            self.assertEqual(serializer.format_time(datetime.time(2, 31, 33)), '02:31:33')

    def test_to_xml(self):
        serializer = Serializer()
        sample_1 = self.get_sample1()
        # This needs a little explanation.
        # From http://lxml.de/parsing.html, what comes out of ``tostring``
        # (despite encoding as UTF-8) is a bytestring. This is because that's
        # what other libraries expect (& will do the decode). We decode here
        # so we can make extra special sure it looks right.
        binary_xml = serializer.to_xml(sample_1)
        unicode_xml = binary_xml.decode('utf-8')
        self.assertEqual(unicode_xml, u'<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><age type="integer">27</age><date_joined>2010-03-27</date_joined><name>Daniel</name><snowman>☃</snowman></response>')

    def test_to_xml2(self):
        serializer = Serializer()
        sample_2 = self.get_sample2()
        binary_xml = serializer.to_xml(sample_2)
        unicode_xml = binary_xml.decode('utf-8')
        self.assertEqual(unicode_xml, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><false type="boolean">False</false><somehash type="hash"><foo>bar</foo><pi type="float">3.14</pi></somehash><somelist type="list"><value>hello</value><value type="integer">1</value><value type="null"/></somelist><somestring>hello</somestring><true type="boolean">True</true></response>')

    def test_from_xml(self):
        serializer = Serializer()
        data = u'<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<request><snowman>☃</snowman><age type="integer">27</age><name>Daniel</name><date_joined>2010-03-27</date_joined><rocksdahouse type="boolean">True</rocksdahouse></request>'
        self.assertEqual(serializer.from_xml(data), {'rocksdahouse': True, 'age': 27, 'name': 'Daniel', 'date_joined': '2010-03-27', 'snowman': u'☃'})

    def test_from_xml2(self):
        serializer = Serializer()
        data = '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<request><somelist type="list"><value>hello</value><value type="integer">1</value><value type="null"/></somelist><somehash type="hash"><pi type="float">3.14</pi><foo>bar</foo></somehash><false type="boolean">False</false><true type="boolean">True</true><somestring>hello</somestring></request>'
        self.assertEqual(serializer.from_xml(data), self.get_sample2())

    def test_malformed_xml(self):
        serializer = Serializer()
        data = '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<request><somelist type="list"><valueNO CARRIER'
        self.assertRaises(BadRequest, serializer.from_xml, data)

    def test_to_json(self):
        serializer = Serializer()

        sample_1 = self.get_sample1()
        self.assertEqual(serializer.to_json(sample_1), u'{"age": 27, "date_joined": "2010-03-27", "name": "Daniel", "snowman": "☃"}')

    def test_from_json(self):
        serializer = Serializer()

        sample_1 = serializer.from_json(u'{"age": 27, "date_joined": "2010-03-27", "name": "Daniel", "snowman": "☃"}')
        self.assertEqual(len(sample_1), 4)
        self.assertEqual(sample_1['name'], 'Daniel')
        self.assertEqual(sample_1['age'], 27)
        self.assertEqual(sample_1['date_joined'], u'2010-03-27')
        self.assertEqual(sample_1['snowman'], u'☃')

    def test_from_broken_json(self):
        serializer = Serializer()
        data = '{"foo": "bar",NO CARRIER'
        self.assertRaises(BadRequest, serializer.from_json, data)

    def test_round_trip_xml(self):
        serializer = Serializer()
        sample_data = self.get_sample2()
        serialized = serializer.to_xml(sample_data)
        # "response" tags need to be changed to "request" to deserialize properly.
        # A string substitution works here.
        serialized = serialized.decode('utf-8').replace('response', 'request')
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

    def test_unsafe_yaml(self):
        serializer = Serializer()
        evil_data = UnsafeObject()
        serialized = yaml.dump(evil_data)
        self.assertRaises(yaml.constructor.ConstructorError,
                          serializer.from_yaml,
                          serialized)

    def test_unsafe_xml(self):
        """
        Entity expansion can be used to cause large memory usage after
        deserialization for little memory usage from the attacker.
        See https://pypi.python.org/pypi/defusedxml for more information.
        """
        serializer = Serializer()
        data = """<!DOCTYPE bomb [<!ENTITY a "evil chars">]>
        <bomb>&a;</bomb>
        """
        self.assertRaises(BadRequest, serializer.from_xml, data)

    def test_to_jsonp(self):
        serializer = Serializer()

        sample_1 = self.get_sample1()
        options = {'callback': 'myCallback'}
        serialized = serializer.to_jsonp(sample_1, options=options)
        serialized_json = serializer.to_json(sample_1)
        self.assertEqual('myCallback(%s)' % serialized_json,
                         serialized)

    def test_invalid_jsonp_characters(self):
        """
        The newline characters \u2028 and \u2029 need to be escaped
        in JSONP.
        """
        serializer = Serializer()

        jsonp = serializer.to_jsonp({'foo': u'Hello \u2028\u2029world!'},
                                    {'callback': 'callback'})
        self.assertEqual(jsonp, u'callback({"foo": "Hello \\u2028\\u2029world!"})')

    @skipIfNoBiplist
    def test_to_plist(self):
        serializer = Serializer()

        sample_1 = self.get_sample1()
        self.assertTrue(serializer.to_plist(sample_1).startswith(b'bplist00bybiplist1.0'))

    @skipIfNoBiplist
    def test_from_plist(self):
        serializer = Serializer()

        sample_1 = serializer.from_plist(b'bplist00bybiplist1.0\x00\xd4\x01\x02\x03\x04\x05\x06\x07\x08WsnowmanSageTname[date_joineda&\x03\x10\x1bf\x00D\x00a\x00n\x00i\x00e\x00lZ2010-03-27\x15\x1e&*/;>@M\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00X')
        self.assertEqual(len(sample_1), 4)
        self.assertEqual(sample_1['name'], 'Daniel')
        self.assertEqual(sample_1['age'], 27)
        self.assertEqual(sample_1['date_joined'], '2010-03-27')
        self.assertEqual(sample_1['snowman'], u'☃')


class ResourceSerializationTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def setUp(self):
        super(ResourceSerializationTestCase, self).setUp()
        self.resource = NoteResource()
        base_bundle = Bundle()
        self.obj_list = [self.resource.full_dehydrate(self.resource.build_bundle(obj=obj)) for obj in self.resource.obj_get_list(base_bundle)]
        self.another_resource = AnotherNoteResource()
        self.another_obj_list = [self.another_resource.full_dehydrate(self.resource.build_bundle(obj=obj)) for obj in self.another_resource.obj_get_list(base_bundle)]

    def test_to_xml_multirepr(self):
        serializer = Serializer()
        binary_xml = serializer.to_xml(self.obj_list)
        unicode_xml = binary_xml.decode('utf-8')
        self.assertEqual(unicode_xml, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<objects><object><content>This is my very first post using my shiny new API. Pretty sweet, huh?</content><created>2010-03-30T20:05:00</created><id type="integer">1</id><is_active type="boolean">True</is_active><resource_uri></resource_uri><slug>first-post</slug><title>First Post!</title><updated>2010-03-30T20:05:00</updated></object><object><content>The dog ate my cat today. He looks seriously uncomfortable.</content><created>2010-03-31T20:05:00</created><id type="integer">2</id><is_active type="boolean">True</is_active><resource_uri></resource_uri><slug>another-post</slug><title>Another Post</title><updated>2010-03-31T20:05:00</updated></object><object><content>My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.</content><created>2010-04-01T20:05:00</created><id type="integer">4</id><is_active type="boolean">True</is_active><resource_uri></resource_uri><slug>recent-volcanic-activity</slug><title>Recent Volcanic Activity.</title><updated>2010-04-01T20:05:00</updated></object><object><content>Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!</content><created>2010-04-02T10:05:00</created><id type="integer">6</id><is_active type="boolean">True</is_active><resource_uri></resource_uri><slug>grannys-gone</slug><title>Granny\'s Gone</title><updated>2010-04-02T10:05:00</updated></object></objects>')

    def test_to_xml_single(self):
        serializer = Serializer()
        resource = self.obj_list[0]
        binary_xml = serializer.to_xml(resource)
        unicode_xml = binary_xml.decode('utf-8')
        self.assertEqual(unicode_xml, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<object><content>This is my very first post using my shiny new API. Pretty sweet, huh?</content><created>2010-03-30T20:05:00</created><id type="integer">1</id><is_active type="boolean">True</is_active><resource_uri></resource_uri><slug>first-post</slug><title>First Post!</title><updated>2010-03-30T20:05:00</updated></object>')

    def test_to_xml_nested(self):
        serializer = Serializer()
        resource = self.obj_list[0]
        data = {
            'stuff': {
                'foo': 'bar',
                'object': resource,
            }
        }
        binary_xml = serializer.to_xml(data)
        unicode_xml = binary_xml.decode('utf-8')
        self.assertEqual(unicode_xml, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><stuff type="hash"><foo>bar</foo><object><content>This is my very first post using my shiny new API. Pretty sweet, huh?</content><created>2010-03-30T20:05:00</created><id type="integer">1</id><is_active type="boolean">True</is_active><resource_uri></resource_uri><slug>first-post</slug><title>First Post!</title><updated>2010-03-30T20:05:00</updated></object></stuff></response>')

    def test_to_json_multirepr(self):
        serializer = Serializer()
        self.assertEqual(serializer.to_json(self.obj_list), '[{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "2010-04-01T20:05:00", "id": 4, "is_active": true, "resource_uri": "", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "2010-04-01T20:05:00"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "2010-04-02T10:05:00", "id": 6, "is_active": true, "resource_uri": "", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "2010-04-02T10:05:00"}]')

    def test_to_json_single(self):
        serializer = Serializer()
        resource = self.obj_list[0]
        self.assertEqual(serializer.to_json(resource), '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}')

    def test_to_json_decimal_list_dict(self):
        serializer = Serializer()
        resource = self.another_obj_list[0]
        self.assertEqual(serializer.to_json(resource), '{"aliases": ["Mr. Smith", "John Doe"], "content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "meta": {"threat": "high"}, "owed": "102.57", "resource_uri": "", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}')

    def test_to_json_nested(self):
        serializer = Serializer()
        resource = self.obj_list[0]
        data = {
            'stuff': {
                'foo': 'bar',
                'object': resource,
            }
        }
        self.assertEqual(serializer.to_json(data), '{"stuff": {"foo": "bar", "object": {"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}}}')


class StubbedSerializer(Serializer):
    def __init__(self, *args, **kwargs):
        super(StubbedSerializer, self).__init__(*args, **kwargs)
        self.from_json_called = False
        self.from_xml_called = False
        self.from_yaml_called = False
        self.from_jsonp_called = False

    def from_json(self, data):
        self.from_json_called = True
        return True

    def from_xml(self, data):
        self.from_xml_called = True
        return True

    def from_yaml(self, data):
        self.from_yaml_called = True
        return True

    def from_jsonp(self, data):
        self.from_jsonp_called = True
        return True


class ContentHeaderTest(TestCase):
    def test_deserialize_json(self):
        serializer = StubbedSerializer()
        serializer.deserialize('{}', 'application/json')
        self.assertTrue(serializer.from_json_called)

    def test_deserialize_json_with_charset(self):
        serializer = StubbedSerializer()
        serializer.deserialize('{}', 'application/json; charset=UTF-8')
        self.assertTrue(serializer.from_json_called)

    def test_deserialize_xml(self):
        serializer = StubbedSerializer()
        serializer.deserialize('', 'application/xml')
        self.assertTrue(serializer.from_xml_called)

    def test_deserialize_xml_with_charset(self):
        serializer = StubbedSerializer()
        serializer.deserialize('', 'application/xml; charset=UTF-8')
        self.assertTrue(serializer.from_xml_called)

    def test_deserialize_yaml(self):
        serializer = StubbedSerializer()
        serializer.deserialize('', 'text/yaml')
        self.assertTrue(serializer.from_yaml_called)

    def test_deserialize_yaml_with_charset(self):
        serializer = StubbedSerializer()
        serializer.deserialize('', 'text/yaml; charset=UTF-8')
        self.assertTrue(serializer.from_yaml_called)

    def test_deserialize_jsonp(self):
        serializer = StubbedSerializer()
        serializer.deserialize('{}', 'text/javascript')
        self.assertTrue(serializer.from_jsonp_called)

    def test_deserialize_jsonp_with_charset(self):
        serializer = StubbedSerializer()
        serializer.deserialize('{}', 'text/javascript; charset=UTF-8')
        self.assertTrue(serializer.from_jsonp_called)
