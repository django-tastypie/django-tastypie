import datetime
from django.test import TestCase
from tastypie import fields
from tastypie.representations.simple import Representation
from tastypie.representations.models import ModelRepresentation


class BasicRepresentation(Representation):
    name = fields.CharField(attribute='name')
    view_count = fields.IntegerField(attribute='view_count', default=0)
    date_joined = fields.DateTimeField(null=True)
    
    def dehydrate_date_joined(self, obj):
        if hasattr(obj, 'date_joined'):
            return obj.date_joined
        
        return datetime.datetime(2010, 3, 27, 22, 30, 0)


class AnotherBasicRepresentation(BasicRepresentation):
    date_joined = fields.DateField(attribute='created')
    is_active = fields.BooleanField(attribute='is_active', default=True)


class RepresentationTestCase(TestCase):
    def test_fields(self):
        basic = BasicRepresentation()
        self.assertEqual(len(basic.fields), 3)
        self.assert_('name' in basic.fields)
        self.assertEqual(isinstance(basic.fields['name'], fields.CharField), True)
        self.assert_('view_count' in basic.fields)
        self.assertEqual(isinstance(basic.fields['view_count'], fields.IntegerField), True)
        self.assert_('date_joined' in basic.fields)
        self.assertEqual(isinstance(basic.fields['date_joined'], fields.DateTimeField), True)
        
        another = AnotherBasicRepresentation()
        self.assertEqual(len(another.fields), 4)
        self.assert_('name' in another.fields)
        self.assertEqual(isinstance(another.fields['name'], fields.CharField), True)
        self.assert_('view_count' in another.fields)
        self.assertEqual(isinstance(another.fields['view_count'], fields.IntegerField), True)
        self.assert_('date_joined' in another.fields)
        self.assertEqual(isinstance(another.fields['date_joined'], fields.DateField), True)
        self.assert_('is_active' in another.fields)
        self.assertEqual(isinstance(another.fields['is_active'], fields.BooleanField), True)
    
    def test_full_dehydrate(self):
        class TestObject(object):
            pass
        
        test_object_1 = TestObject()
        test_object_1.name = 'Daniel'
        test_object_1.view_count = 12
        test_object_1.date_joined = datetime.datetime(2010, 3, 30, 9, 0, 0)
        test_object_1.foo = "Hi, I'm ignored."
        
        basic = BasicRepresentation()
        
        # Sanity check.
        self.assertEqual(basic.fields['name'].value, None)
        self.assertEqual(basic.fields['view_count'].value, None)
        self.assertEqual(basic.fields['date_joined'].value, None)
        
        basic.full_dehydrate(test_object_1)
        self.assertEqual(basic.fields['name'].value, 'Daniel')
        self.assertEqual(basic.fields['view_count'].value, 12)
        self.assertEqual(basic.fields['date_joined'].value.year, 2010)
        self.assertEqual(basic.fields['date_joined'].value.day, 30)
        
        # Now check the fallback behaviors.
        test_object_2 = TestObject()
        test_object_2.name = 'Daniel'
        basic_2 = BasicRepresentation()
        
        # Sanity check.
        self.assertEqual(basic_2.fields['name'].value, None)
        self.assertEqual(basic_2.fields['view_count'].value, None)
        self.assertEqual(basic_2.fields['date_joined'].value, None)
        
        basic_2.full_dehydrate(test_object_2)
        self.assertEqual(basic_2.fields['name'].value, 'Daniel')
        self.assertEqual(basic_2.fields['view_count'].value, 0)
        self.assertEqual(basic_2.fields['date_joined'].value.year, 2010)
        self.assertEqual(basic_2.fields['date_joined'].value.day, 27)
    
    def test_full_hydrate(self):
        pass


class ModelRepresentationTestCase(TestCase):
    def test_configuration(self):
        pass
    
    def test_get_list(self):
        pass
    
    def test_get(self):
        pass
    
    def test_create(self):
        pass
    
    def test_update(self):
        pass
    
    def test_delete(self):
        pass
