from django.test import TestCase
from tastypie.fields import *


class ApiFieldTestCase(TestCase):
    def test_init(self):
        field_1 = ApiField()
        self.assertEqual(field_1.instance_name, None)
        self.assertEqual(field_1.attribute, None)
        self.assertEqual(field_1._default, NOT_PROVIDED)
        self.assertEqual(field_1.null, False)
        self.assertEqual(field_1.value, None)
        
        field_2 = ApiField(attribute='foo', default=True, null=True)
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(field_2.attribute, 'foo')
        self.assertEqual(field_2._default, True)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.value, None)
    
    def test_has_default(self):
        field_1 = ApiField()
        self.assertEqual(field_1.has_default(), False)
        
        field_2 = ApiField(default=True)
        self.assertEqual(field_2.has_default(), True)
    
    def test_default(self):
        field_1 = ApiField()
        self.assertEqual(isinstance(field_1.default, NOT_PROVIDED), True)
        
        field_2 = ApiField(default=True)
        self.assertEqual(field_2.default, True)
    
    def test_dehydrate(self):
        pass
    
    def test_convert(self):
        pass
    
    def test_hydrate(self):
        pass


class CharFieldTestCase(TestCase):
    def test_init(self):
        pass
