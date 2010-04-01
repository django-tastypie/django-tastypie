import datetime
from django.test import TestCase
from tastypie.exceptions import ApiFieldError
from tastypie.fields import *
from core.models import Note


class ApiFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
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
        note = Note.objects.get(pk=1)
        
        # With no attribute or default, we should get ``None``.
        field_1 = ApiField()
        self.assertEqual(field_1.dehydrate(note), None)
        
        # Still no attribute, so we should pick up the default
        field_2 = ApiField(default=True)
        self.assertEqual(field_2.dehydrate(note), True)
        
        # Wrong attribute should yield default.
        field_3 = ApiField(attribute='foo', default=True)
        self.assertEqual(field_3.dehydrate(note), True)
        
        # Wrong attribute should yield null.
        field_4 = ApiField(attribute='foo', null=True)
        self.assertEqual(field_4.dehydrate(note), None)
        
        # Correct attribute.
        field_5 = ApiField(attribute='title', default=True)
        self.assertEqual(field_5.dehydrate(note), u'First Post!')
        
        # Correct callable attribute.
        field_6 = ApiField(attribute='what_time_is_it', default=True)
        self.assertEqual(field_6.dehydrate(note), datetime.datetime(2010, 4, 1, 0, 48))
    
    def test_convert(self):
        field_1 = ApiField()
        self.assertEqual(field_1.convert('foo'), 'foo')
        self.assertEqual(field_1.convert(True), True)
    
    def test_hydrate(self):
        note = Note.objects.get(pk=1)
        
        # With no value, default or nullable, we should get an ``ApiFieldError``.
        field_1 = ApiField()
        field_1.value = None
        self.assertRaises(ApiFieldError, field_1.hydrate)
        
        # The default.
        field_2 = ApiField(default='foo')
        field_2.value = None
        self.assertEqual(field_2.hydrate(), 'foo')
        
        # The callable default.
        def foo():
            return 'bar'
        
        field_3 = ApiField(default=foo)
        field_3.value = None
        self.assertEqual(field_3.hydrate(), 'bar')
        
        # The nullable case.
        field_4 = ApiField(null=True)
        field_4.value = None
        self.assertEqual(field_4.hydrate(), None)
        
        # A real, live attribute!
        field_5 = ApiField(attribute='title')
        field_5.value = note.title
        self.assertEqual(field_5.hydrate(), u'First Post!')


class CharFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        
        field_1 = CharField(attribute='title', default=True)
        self.assertEqual(field_1.dehydrate(note), u'First Post!')
        
        field_2 = CharField(default=20)
        self.assertEqual(field_2.dehydrate(note), u'20')


class IntegerFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        
        field_1 = IntegerField(default=25)
        self.assertEqual(field_1.dehydrate(note), 25)
        
        field_2 = IntegerField(default='20')
        self.assertEqual(field_2.dehydrate(note), 20)
        
        field_3 = IntegerField(default=18.5)
        self.assertEqual(field_3.dehydrate(note), 18)


class FloatFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        
        field_1 = FloatField(default=20)
        self.assertEqual(field_1.dehydrate(note), 20.0)
        
        field_2 = IntegerField(default=18.5)
        self.assertEqual(field_2.dehydrate(note), 18)


class BooleanFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        
        field_1 = BooleanField(attribute='is_active', default=False)
        self.assertEqual(field_1.dehydrate(note), True)
        
        field_2 = BooleanField(default=True)
        self.assertEqual(field_2.dehydrate(note), True)


class DateFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        
        field_1 = DateField(attribute='created')
        self.assertEqual(field_1.dehydrate(note), datetime.datetime(2010, 3, 30, 20, 5))
        
        field_2 = DateField(default=datetime.date(2010, 4, 1))
        self.assertEqual(field_2.dehydrate(note), datetime.date(2010, 4, 1))
        
        note.created_string = '2010-04-02'
        field_3 = DateField(attribute='created_string')
        self.assertEqual(field_3.dehydrate(note), datetime.date(2010, 4, 2))


class DateTimeFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        
        field_1 = DateField(attribute='created')
        self.assertEqual(field_1.dehydrate(note), datetime.datetime(2010, 3, 30, 20, 5))
        
        field_2 = DateField(default=datetime.datetime(2010, 4, 1, 1, 7))
        self.assertEqual(field_2.dehydrate(note), datetime.datetime(2010, 4, 1, 1, 7))
        
        note.created_string = '2010-04-02 01:11:00'
        field_3 = DateField(attribute='created_string')
        self.assertEqual(field_3.dehydrate(note), datetime.datetime(2010, 4, 2, 1, 11))
