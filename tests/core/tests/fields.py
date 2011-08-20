import datetime
from dateutil.tz import *
from django.db import models
from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.bundle import Bundle
from tastypie.exceptions import ApiFieldError, NotFound
from tastypie.fields import *
from tastypie.resources import ModelResource
from core.models import Note, Subject, MediaBit


class ApiFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = ApiField()
        self.assertEqual(field_1.instance_name, None)
        self.assertEqual(field_1.attribute, None)
        self.assertEqual(field_1._default, NOT_PROVIDED)
        self.assertEqual(field_1.null, False)
        self.assertEqual(field_1.value, None)
        self.assertEqual(field_1.help_text, '')

        field_2 = ApiField(attribute='foo', default=True, null=True, readonly=True, help_text='Foo.')
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(field_2.attribute, 'foo')
        self.assertEqual(field_2._default, True)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.value, None)
        self.assertEqual(field_2.readonly, True)
        self.assertEqual(field_2.help_text, 'Foo.')

    def test_dehydrated_type(self):
        field_1 = ApiField()
        self.assertEqual(field_1.dehydrated_type, 'string')

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
        bundle = Bundle(obj=note)

        # With no attribute or default, we should get ``None``.
        field_1 = ApiField()
        self.assertEqual(field_1.dehydrate(bundle), None)

        # Still no attribute, so we should pick up the default
        field_2 = ApiField(default=True)
        self.assertEqual(field_2.dehydrate(bundle), True)

        # Wrong attribute should yield default.
        field_3 = ApiField(attribute='foo', default=True)
        self.assertEqual(field_3.dehydrate(bundle), True)

        # Wrong attribute should yield null.
        field_4 = ApiField(attribute='foo', null=True)
        self.assertEqual(field_4.dehydrate(bundle), None)

        # Correct attribute.
        field_5 = ApiField(attribute='title', default=True)
        self.assertEqual(field_5.dehydrate(bundle), u'First Post!')

        # Correct callable attribute.
        field_6 = ApiField(attribute='what_time_is_it', default=True)
        self.assertEqual(field_6.dehydrate(bundle), datetime.datetime(2010, 4, 1, 0, 48))

    def test_convert(self):
        field_1 = ApiField()
        self.assertEqual(field_1.convert('foo'), 'foo')
        self.assertEqual(field_1.convert(True), True)

    def test_hydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        # With no value, default or nullable, we should get an ``ApiFieldError``.
        field_1 = ApiField()
        field_1.instance_name = 'api'
        self.assertRaises(ApiFieldError, field_1.hydrate, bundle)

        # The default.
        field_2 = ApiField(default='foo')
        field_2.instance_name = 'api'
        self.assertEqual(field_2.hydrate(bundle), 'foo')

        # The callable default.
        def foo():
            return 'bar'

        field_3 = ApiField(default=foo)
        field_3.instance_name = 'api'
        self.assertEqual(field_3.hydrate(bundle), 'bar')

        # The nullable case.
        field_4 = ApiField(null=True)
        field_4.instance_name = 'api'
        self.assertEqual(field_4.hydrate(bundle), None)

        # The readonly case.
        field_5 = ApiField(readonly=True)
        field_5.instance_name = 'api'
        bundle.data['api'] = 'abcdef'
        self.assertEqual(field_5.hydrate(bundle), None)

        # A real, live attribute!
        field_6 = ApiField(attribute='title')
        field_6.instance_name = 'api'
        bundle.data['api'] = note.title
        self.assertEqual(field_6.hydrate(bundle), u'First Post!')

        # Make sure it uses attribute when there's no data
        field_7 = ApiField(attribute='title')
        field_7.instance_name = 'notinbundle'
        self.assertEqual(field_7.hydrate(bundle), u'First Post!')

        # Make sure it falls back to instance name if there is no attribute
        field_8 = ApiField()
        field_8.instance_name = 'title'
        self.assertEqual(field_8.hydrate(bundle), u'First Post!')

        # Attribute & null regression test.
        # First, simulate data missing from the bundle & ``null=True``.
        field_9 = ApiField(attribute='notinbundle', null=True)
        field_9.instance_name = 'notinbundle'
        self.assertEqual(field_9.hydrate(bundle), None)
        # The do something in the bundle also with ``null=True``.
        field_10 = ApiField(attribute='title', null=True)
        field_10.instance_name = 'title'
        self.assertEqual(field_10.hydrate(bundle), u'First Post!')

        # The blank case.
        field_11 = ApiField(attribute='notinbundle', blank=True)
        field_11.instance_name = 'notinbundle'
        self.assertEqual(field_11.hydrate(bundle), None)

        bundle.data['title'] = note.title
        field_12 = ApiField(attribute='title', blank=True)
        field_12.instance_name = 'title'
        self.assertEqual(field_12.hydrate(bundle), u'First Post!')


class CharFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = CharField()
        self.assertEqual(field_1.help_text, 'Unicode string data. Ex: "Hello World"')

        field_2 = CharField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = CharField()
        self.assertEqual(field_1.dehydrated_type, 'string')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = CharField(attribute='title', default=True)
        self.assertEqual(field_1.dehydrate(bundle), u'First Post!')

        field_2 = CharField(default=20)
        self.assertEqual(field_2.dehydrate(bundle), u'20')


class FileFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = FileField()
        self.assertEqual(field_1.help_text, 'A file URL as a string. Ex: "http://media.example.com/media/photos/my_photo.jpg"')

        field_2 = FileField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = FileField()
        self.assertEqual(field_1.dehydrated_type, 'string')

    def test_dehydrate(self):
        bit = MediaBit.objects.get(pk=1)
        bundle = Bundle(obj=bit)

        field_1 = FileField(attribute='image', default=True)
        self.assertEqual(field_1.dehydrate(bundle), u'http://localhost:8080/media/lulz/catz.gif')

        field_2 = FileField(default='http://media.example.com/img/default_avatar.jpg')
        self.assertEqual(field_2.dehydrate(bundle), u'http://media.example.com/img/default_avatar.jpg')

        bit = MediaBit.objects.get(pk=1)
        bit.image = ''
        bundle = Bundle(obj=bit)

        field_3 = FileField(attribute='image', default=True)
        self.assertEqual(field_3.dehydrate(bundle), None)

        bit.image = None
        bundle = Bundle(obj=bit)

        field_4 = FileField(attribute='image', null=True)
        self.assertEqual(field_4.dehydrate(bundle), None)


class IntegerFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = IntegerField()
        self.assertEqual(field_1.help_text, 'Integer data. Ex: 2673')

        field_2 = IntegerField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = IntegerField()
        self.assertEqual(field_1.dehydrated_type, 'integer')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = IntegerField(default=25)
        self.assertEqual(field_1.dehydrate(bundle), 25)

        field_2 = IntegerField(default='20')
        self.assertEqual(field_2.dehydrate(bundle), 20)

        field_3 = IntegerField(default=18.5)
        self.assertEqual(field_3.dehydrate(bundle), 18)


class FloatFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = FloatField()
        self.assertEqual(field_1.help_text, 'Floating point numeric data. Ex: 26.73')

        field_2 = FloatField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = FloatField()
        self.assertEqual(field_1.dehydrated_type, 'float')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = FloatField(default=20)
        self.assertEqual(field_1.dehydrate(bundle), 20.0)

        field_2 = IntegerField(default=18.5)
        self.assertEqual(field_2.dehydrate(bundle), 18)


class DecimalFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = DecimalField()
        self.assertEqual(field_1.help_text, 'Fixed precision numeric data. Ex: 26.73')

        field_2 = DecimalField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = DecimalField()
        self.assertEqual(field_1.dehydrated_type, 'decimal')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = DecimalField(default='20')
        self.assertEqual(field_1.dehydrate(bundle), Decimal('20.0'))

        field_2 = DecimalField(default='18.5')
        self.assertEqual(field_2.dehydrate(bundle), Decimal('18.5'))

    def test_model_resource_correct_association(self):
        api_field = ModelResource.api_field_from_django_field(models.DecimalField())
        self.assertEqual(api_field, DecimalField)


class ListFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = ListField()
        self.assertEqual(field_1.help_text, "A list of data. Ex: ['abc', 26.73, 8]")

        field_2 = ListField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = ListField()
        self.assertEqual(field_1.dehydrated_type, 'list')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = ListField(default=[1, 2, 3])
        self.assertEqual(field_1.dehydrate(bundle), [1, 2, 3])

        field_2 = ListField(default=['abc'])
        self.assertEqual(field_2.dehydrate(bundle), ['abc'])


class DictFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = DictField()
        self.assertEqual(field_1.help_text, "A dictionary of data. Ex: {'price': 26.73, 'name': 'Daniel'}")

        field_2 = DictField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = DictField()
        self.assertEqual(field_1.dehydrated_type, 'dict')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = DictField(default={'price': 12.34, 'name': 'Daniel'})
        self.assertEqual(field_1.dehydrate(bundle), {'price': 12.34, 'name': 'Daniel'})

        field_2 = DictField(default={'name': 'Daniel'})
        self.assertEqual(field_2.dehydrate(bundle), {'name': 'Daniel'})


class BooleanFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = BooleanField()
        self.assertEqual(field_1.help_text, 'Boolean data. Ex: True')

        field_2 = BooleanField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = BooleanField()
        self.assertEqual(field_1.dehydrated_type, 'boolean')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = BooleanField(attribute='is_active', default=False)
        self.assertEqual(field_1.dehydrate(bundle), True)

        field_2 = BooleanField(default=True)
        self.assertEqual(field_2.dehydrate(bundle), True)


class TimeFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = TimeField()
        self.assertEqual(field_1.help_text, 'A time as string. Ex: "20:05:23"')
        field_2 = TimeField(help_text='Custom.')
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = TimeField()
        self.assertEqual(field_1.dehydrated_type, 'time')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = TimeField(attribute='created')
        self.assertEqual(field_1.dehydrate(bundle), datetime.datetime(2010, 3, 30, 20, 5))

        field_2 = TimeField(default=datetime.time(23, 5, 58))
        self.assertEqual(field_2.dehydrate(bundle), datetime.time(23, 5, 58))

        field_3 = TimeField(attribute='created_string')

        note.created_string = '13:06:00'
        self.assertEqual(field_3.dehydrate(bundle), datetime.time(13, 6))

        note.created_string = '13:37:44'
        self.assertEqual(field_3.dehydrate(bundle), datetime.time(13, 37, 44))

        note.created_string = 'hello'
        self.assertRaises(ApiFieldError, field_3.dehydrate, bundle)

    def test_hydrate(self):
        bundle_1 = Bundle(data={'time': '03:49'})
        field_1 = TimeField(attribute='created')
        field_1.instance_name = 'time'
        self.assertEqual(field_1.hydrate(bundle_1), datetime.time(3, 49))

        bundle_2 = Bundle()
        field_2 = TimeField(default=datetime.time(17, 40))
        field_2.instance_name = 'doesnotmatter'  # Wont find in bundle data
        self.assertEqual(field_2.hydrate(bundle_2), datetime.time(17, 40))

        bundle_3 = Bundle(data={'time': '22:08:11'})
        field_3 = TimeField(attribute='created_string')
        field_3.instance_name = 'time'
        self.assertEqual(field_3.hydrate(bundle_3), datetime.time(22, 8, 11))

        bundle_4 = Bundle(data={'time': '07:45'})
        field_4 = TimeField(attribute='created')
        field_4.instance_name = 'time'
        self.assertEqual(field_4.hydrate(bundle_4), datetime.time(7, 45))

        bundle_5 = Bundle(data={'time': None})
        field_5 = TimeField(attribute='created', null=True)
        field_5.instance_name = 'time'
        self.assertEqual(field_5.hydrate(bundle_5), None)


class DateFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = CharField()
        self.assertEqual(field_1.help_text, 'Unicode string data. Ex: "Hello World"')

        field_2 = CharField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = DateField()
        self.assertEqual(field_1.dehydrated_type, 'date')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = DateField(attribute='created')
        self.assertEqual(field_1.dehydrate(bundle), datetime.datetime(2010, 3, 30, 20, 5))

        field_2 = DateField(default=datetime.date(2010, 4, 1))
        self.assertEqual(field_2.dehydrate(bundle), datetime.date(2010, 4, 1))

        note.created_string = '2010-04-02'
        field_3 = DateField(attribute='created_string')
        self.assertEqual(field_3.dehydrate(bundle), datetime.date(2010, 4, 2))

    def test_hydrate(self):
        note = Note.objects.get(pk=1)

        bundle_1 = Bundle(data={
            'date': '2010-05-12',
        })
        field_1 = DateField(attribute='created')
        field_1.instance_name = 'date'
        self.assertEqual(field_1.hydrate(bundle_1), datetime.date(2010, 5, 12))

        bundle_2 = Bundle()
        field_2 = DateField(default=datetime.date(2010, 4, 1))
        field_2.instance_name = 'date'
        self.assertEqual(field_2.hydrate(bundle_2), datetime.date(2010, 4, 1))

        bundle_3 = Bundle(data={
            'date': 'Wednesday, May 12, 2010',
        })
        field_3 = DateField(attribute='created_string')
        field_3.instance_name = 'date'
        self.assertEqual(field_3.hydrate(bundle_3), datetime.date(2010, 5, 12))

        bundle_4 = Bundle(data={
            'date': '5 Apr 2010',
        })
        field_4 = DateField(attribute='created')
        field_4.instance_name = 'date'
        self.assertEqual(field_4.hydrate(bundle_4), datetime.date(2010, 4, 5))

        bundle_5 = Bundle(data={
            'date': None,
        })
        field_5 = DateField(attribute='created', null=True)
        field_5.instance_name = 'date'
        self.assertEqual(field_5.hydrate(bundle_5), None)


class DateTimeFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = CharField()
        self.assertEqual(field_1.help_text, 'Unicode string data. Ex: "Hello World"')

        field_2 = CharField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')

    def test_dehydrated_type(self):
        field_1 = DateTimeField()
        self.assertEqual(field_1.dehydrated_type, 'datetime')

    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_1 = DateTimeField(attribute='created')
        self.assertEqual(field_1.dehydrate(bundle), datetime.datetime(2010, 3, 30, 20, 5))

        field_2 = DateTimeField(default=datetime.datetime(2010, 4, 1, 1, 7))
        self.assertEqual(field_2.dehydrate(bundle), datetime.datetime(2010, 4, 1, 1, 7))

        note.created_string = '2010-04-02 01:11:00'
        field_3 = DateTimeField(attribute='created_string')
        self.assertEqual(field_3.dehydrate(bundle), datetime.datetime(2010, 4, 2, 1, 11))

    def test_hydrate(self):
        note = Note.objects.get(pk=1)

        bundle_1 = Bundle(data={
            'datetime': '2010-05-12 10:36:28',
        })
        field_1 = DateTimeField(attribute='created')
        field_1.instance_name = 'datetime'
        self.assertEqual(field_1.hydrate(bundle_1), datetime.datetime(2010, 5, 12, 10, 36, 28))

        bundle_2 = Bundle()
        field_2 = DateTimeField(default=datetime.datetime(2010, 4, 1, 2, 0))
        field_2.instance_name = 'datetime'
        self.assertEqual(field_2.hydrate(bundle_2), datetime.datetime(2010, 4, 1, 2, 0))

        bundle_3 = Bundle(data={
            'datetime': 'Tue, 30 Mar 2010 20:05:00 -0500',
        })
        field_3 = DateTimeField(attribute='created_string')
        field_3.instance_name = 'datetime'
        self.assertEqual(field_3.hydrate(bundle_3), datetime.datetime(2010, 3, 30, 20, 5, tzinfo=tzoffset(None, -18000)))

        bundle_4 = Bundle(data={
            'datetime': None,
        })
        field_4 = DateField(attribute='created', null=True)
        field_4.instance_name = 'datetime'
        self.assertEqual(field_4.hydrate(bundle_4), None)


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()

    def get_resource_uri(self, bundle):
        return '/api/v1/users/%s/' % bundle.obj.id


class ToOneFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_init(self):
        field_1 = ToOneField(UserResource, 'author')
        self.assertEqual(field_1.instance_name, None)
        self.assertEqual(issubclass(field_1.to, UserResource), True)
        self.assertEqual(field_1.attribute, 'author')
        self.assertEqual(field_1.related_name, None)
        self.assertEqual(field_1.null, False)
        self.assertEqual(field_1.full, False)
        self.assertEqual(field_1.readonly, False)
        self.assertEqual(field_1.help_text, 'A single related resource. Can be either a URI or set of nested resource data.')

        field_2 = ToOneField(UserResource, 'author', null=True, help_text="Points to a User.")
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(issubclass(field_2.to, UserResource), True)
        self.assertEqual(field_2.attribute, 'author')
        self.assertEqual(field_2.related_name, None)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.full, False)
        self.assertEqual(field_2.readonly, False)
        self.assertEqual(field_2.help_text, 'Points to a User.')

        field_3 = ToOneField(UserResource, 'author', default=1, null=True, help_text="Points to a User.")
        self.assertEqual(field_3.instance_name, None)
        self.assertEqual(issubclass(field_3.to, UserResource), True)
        self.assertEqual(field_3.attribute, 'author')
        self.assertEqual(field_3.related_name, None)
        self.assertEqual(field_3.null, True)
        self.assertEqual(field_3.default, 1)
        self.assertEqual(field_3.full, False)
        self.assertEqual(field_3.readonly, False)
        self.assertEqual(field_3.help_text, 'Points to a User.')

        field_4 = ToOneField(UserResource, 'author', default=1, null=True, readonly=True, help_text="Points to a User.")
        self.assertEqual(field_4.instance_name, None)
        self.assertEqual(issubclass(field_4.to, UserResource), True)
        self.assertEqual(field_4.attribute, 'author')
        self.assertEqual(field_4.related_name, None)
        self.assertEqual(field_4.null, True)
        self.assertEqual(field_4.default, 1)
        self.assertEqual(field_4.full, False)
        self.assertEqual(field_4.readonly, True)
        self.assertEqual(field_4.help_text, 'Points to a User.')

    def test_dehydrated_type(self):
        field_1 = ToOneField(UserResource, 'author')
        self.assertEqual(field_1.dehydrated_type, 'related')

    def test_has_default(self):
        field_1 = ToOneField(UserResource, 'author')
        self.assertEqual(field_1.has_default(), False)

        field_1 = ToOneField(UserResource, 'author', default=1)
        self.assertEqual(field_1.has_default(), True)

    def test_default(self):
        field_1 = ToOneField(UserResource, 'author')
        self.assertTrue(isinstance(field_1.default, NOT_PROVIDED))

        field_2 = ToOneField(UserResource, 'author', default=1)
        self.assertEqual(field_2.default, 1)

    def test_dehydrate(self):
        note = Note()
        bundle = Bundle(obj=note)

        field_1 = ToOneField(UserResource, 'author')
        self.assertRaises(ApiFieldError, field_1.dehydrate, bundle)

        field_2 = ToOneField(UserResource, 'author', null=True)
        self.assertEqual(field_2.dehydrate(bundle), None)

        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        field_3 = ToOneField(UserResource, 'author')
        self.assertEqual(field_3.dehydrate(bundle), '/api/v1/users/1/')

        field_4 = ToOneField(UserResource, 'author', full=True)
        user_bundle = field_4.dehydrate(bundle)
        self.assertEqual(isinstance(user_bundle, Bundle), True)
        self.assertEqual(user_bundle.data['username'], u'johndoe')
        self.assertEqual(user_bundle.data['email'], u'john@doe.com')

    def test_hydrate(self):
        note = Note()
        bundle = Bundle(obj=note)

        # With no value or nullable, we should get an ``ApiFieldError``.
        field_1 = ToOneField(UserResource, 'author')
        self.assertRaises(ApiFieldError, field_1.hydrate, bundle)

        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        # The nullable case.
        field_2 = ToOneField(UserResource, 'author', null=True)
        field_2.instance_name = 'fk'
        bundle.data['fk'] = None
        self.assertEqual(field_2.hydrate(bundle), None)

        # Wrong resource URI.
        field_3 = ToOneField(UserResource, 'author')
        field_3.instance_name = 'fk'
        bundle.data['fk'] = '/api/v1/users/abc/'
        self.assertRaises(NotFound, field_3.hydrate, bundle)

        # A real, live attribute!
        field_4 = ToOneField(UserResource, 'author')
        field_4.instance_name = 'fk'
        bundle.data['fk'] = '/api/v1/users/1/'
        fk_bundle = field_4.hydrate(bundle)
        self.assertEqual(fk_bundle.data['username'], u'johndoe')
        self.assertEqual(fk_bundle.data['email'], u'john@doe.com')
        self.assertEqual(fk_bundle.obj.username, u'johndoe')
        self.assertEqual(fk_bundle.obj.email, u'john@doe.com')

        field_5 = ToOneField(UserResource, 'author')
        field_5.instance_name = 'fk'
        bundle.data['fk'] = {
            'username': u'mistersmith',
            'email': u'smith@example.com',
            'password': u'foobar',
        }
        fk_bundle = field_5.hydrate(bundle)
        self.assertEqual(fk_bundle.data['username'], u'mistersmith')
        self.assertEqual(fk_bundle.data['email'], u'smith@example.com')
        self.assertEqual(fk_bundle.obj.username, u'mistersmith')
        self.assertEqual(fk_bundle.obj.email, u'smith@example.com')

        # Regression - Make sure Unicode keys get converted to regular strings
        #              so that we can **kwargs them.
        field_6 = ToOneField(UserResource, 'author')
        field_6.instance_name = 'fk'
        bundle.data['fk'] = {
            u'username': u'mistersmith',
            u'email': u'smith@example.com',
            u'password': u'foobar',
        }
        fk_bundle = field_6.hydrate(bundle)
        self.assertEqual(fk_bundle.data['username'], u'mistersmith')
        self.assertEqual(fk_bundle.data['email'], u'smith@example.com')
        self.assertEqual(fk_bundle.obj.username, u'mistersmith')
        self.assertEqual(fk_bundle.obj.email, u'smith@example.com')

        # Attribute & null regression test.
        # First, simulate data missing from the bundle & ``null=True``.
        # Use a Note with NO author, so that the lookup for the related
        # author fails.
        note = Note.objects.create(
            title='Biplanes for all!',
            slug='biplanes-for-all',
            content='Somewhere, east of Manhattan, will lie the mythical land of planes with more one wing...'
        )
        bundle = Bundle(obj=note)
        field_7 = ToOneField(UserResource, 'notinbundle', null=True)
        field_7.instance_name = 'notinbundle'
        self.assertEqual(field_7.hydrate(bundle), None)
        # Then do something in the bundle also with ``null=True``.
        field_8 = ToOneField(UserResource, 'author', null=True)
        field_8.instance_name = 'author'
        fk_bundle = field_8.hydrate(bundle)
        self.assertEqual(field_8.hydrate(bundle), None)
        # Then use an unsaved object in the bundle also with ``null=True``.
        new_note = Note(
            title='Biplanes for all!',
            slug='biplanes-for-all',
            content='Somewhere, east of Manhattan, will lie the mythical land of planes with more one wing...'
        )
        new_bundle = Bundle(obj=new_note)
        field_9 = ToOneField(UserResource, 'author', null=True)
        field_9.instance_name = 'author'
        self.assertEqual(field_9.hydrate(bundle), None)

        # The blank case.
        field_10 = ToOneField(UserResource, 'fk', blank=True)
        field_10.instance_name = 'fk'
        self.assertEqual(field_10.hydrate(bundle), None)

        bundle.data['author'] = '/api/v1/users/1/'
        field_11 = ToOneField(UserResource, 'author', blank=True)
        field_11.instance_name = 'author'
        fk_bundle = field_11.hydrate(bundle)
        self.assertEqual(fk_bundle.obj.username, 'johndoe')

        # The readonly case.
        field_12 = ToOneField(UserResource, 'author', readonly=True)
        field_12.instance_name = 'author'
        self.assertEqual(field_12.hydrate(bundle), None)

    def test_resource_from_uri(self):
        ur = UserResource()
        field_1 = ToOneField(UserResource, 'author')
        fk_bundle = field_1.resource_from_uri(ur, '/api/v1/users/1/')
        self.assertEqual(fk_bundle.data['username'], u'johndoe')
        self.assertEqual(fk_bundle.data['email'], u'john@doe.com')
        self.assertEqual(fk_bundle.obj.username, u'johndoe')
        self.assertEqual(fk_bundle.obj.email, u'john@doe.com')

    def test_resource_from_data(self):
        ur = UserResource()
        field_1 = ToOneField(UserResource, 'author')
        fk_bundle = field_1.resource_from_data(ur, {
            'username': u'mistersmith',
            'email': u'smith@example.com',
            'password': u'foobar',
        })
        self.assertEqual(fk_bundle.data['username'], u'mistersmith')
        self.assertEqual(fk_bundle.data['email'], u'smith@example.com')
        self.assertEqual(fk_bundle.obj.username, u'mistersmith')
        self.assertEqual(fk_bundle.obj.email, u'smith@example.com')

    def test_resource_from_pk(self):
        user = User.objects.get(pk=1)
        ur = UserResource()
        field_1 = ToOneField(UserResource, 'author')
        fk_bundle = field_1.resource_from_pk(ur, user)
        self.assertEqual(fk_bundle.data['username'], u'johndoe')
        self.assertEqual(fk_bundle.data['email'], u'john@doe.com')
        self.assertEqual(fk_bundle.obj.username, u'johndoe')
        self.assertEqual(fk_bundle.obj.email, u'john@doe.com')


class SubjectResource(ModelResource):
    class Meta:
        resource_name = 'subjects'
        queryset = Subject.objects.all()

    def get_resource_uri(self, bundle):
        return '/api/v1/subjects/%s/' % bundle.obj.id


class ToManyFieldTestCase(TestCase):
    fixtures = ['note_testdata.json']
    urls = 'core.tests.field_urls'

    def setUp(self):
        self.note_1 = Note.objects.get(pk=1)
        self.note_2 = Note.objects.get(pk=2)
        self.note_3 = Note.objects.get(pk=3)

        self.subject_1 = Subject.objects.create(
            name='News',
            url='/news/'
        )
        self.subject_2 = Subject.objects.create(
            name='Photos',
            url='/photos/'
        )
        self.subject_3 = Subject.objects.create(
            name='Personal Interest',
            url='/news/personal-interest/'
        )

        self.note_1.subjects.add(self.subject_1)
        self.note_1.subjects.add(self.subject_2)
        self.note_2.subjects.add(self.subject_1)
        self.note_2.subjects.add(self.subject_3)

    def test_init(self):
        field_1 = ToManyField(SubjectResource, 'subjects')
        self.assertEqual(field_1.instance_name, None)
        self.assertEqual(issubclass(field_1.to, SubjectResource), True)
        self.assertEqual(field_1.attribute, 'subjects')
        self.assertEqual(field_1.related_name, None)
        self.assertEqual(field_1.null, False)
        self.assertEqual(field_1.full, False)
        self.assertEqual(field_1.readonly, False)
        self.assertEqual(field_1.help_text, 'Many related resources. Can be either a list of URIs or list of individually nested resource data.')

        field_2 = ToManyField(SubjectResource, 'subjects', null=True, help_text='Points to many Subjects.')
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(issubclass(field_2.to, SubjectResource), True)
        self.assertEqual(field_2.attribute, 'subjects')
        self.assertEqual(field_2.related_name, None)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.full, False)
        self.assertEqual(field_2.readonly, False)
        self.assertEqual(field_2.help_text, 'Points to many Subjects.')

        field_3 = ToManyField(SubjectResource, 'subjects', default=1, null=True, help_text='Points to many Subjects.')
        self.assertEqual(field_3.instance_name, None)
        self.assertEqual(issubclass(field_3.to, SubjectResource), True)
        self.assertEqual(field_3.attribute, 'subjects')
        self.assertEqual(field_3.related_name, None)
        self.assertEqual(field_3.null, True)
        self.assertEqual(field_3.default, 1)
        self.assertEqual(field_3.full, False)
        self.assertEqual(field_3.readonly, False)
        self.assertEqual(field_3.help_text, 'Points to many Subjects.')

        field_4 = ToManyField(SubjectResource, 'subjects', default=1, null=True, readonly=True, help_text='Points to many Subjects.')
        self.assertEqual(field_4.instance_name, None)
        self.assertEqual(issubclass(field_4.to, SubjectResource), True)
        self.assertEqual(field_4.attribute, 'subjects')
        self.assertEqual(field_4.related_name, None)
        self.assertEqual(field_4.null, True)
        self.assertEqual(field_4.default, 1)
        self.assertEqual(field_4.full, False)
        self.assertEqual(field_4.readonly, True)
        self.assertEqual(field_4.help_text, 'Points to many Subjects.')

    def test_dehydrated_type(self):
        field_1 = ToManyField(SubjectResource, 'subjects')
        self.assertEqual(field_1.dehydrated_type, 'related')

    def test_has_default(self):
        field_1 = ToManyField(SubjectResource, 'subjects')
        self.assertEqual(field_1.has_default(), False)

        field_2 = ToManyField(SubjectResource, 'subjects', default=1)
        self.assertEqual(field_2.has_default(), True)

    def test_default(self):
        field_1 = ToManyField(SubjectResource, 'subjects')
        self.assertTrue(isinstance(field_1.default, NOT_PROVIDED))

        field_2 = ToManyField(SubjectResource, 'subjects', default=1)
        self.assertEqual(field_2.default, 1)

    def test_dehydrate(self):
        note = Note()
        bundle_1 = Bundle(obj=note)
        field_1 = ToManyField(SubjectResource, 'subjects')
        field_1.instance_name = 'm2m'

        try:
            # self.assertRaises isn't cooperating here. Do it the hard way.
            field_1.dehydrate(bundle_1)
            self.fail()
        except ApiFieldError:
            pass

        field_2 = ToManyField(SubjectResource, 'subjects', null=True)
        field_2.instance_name = 'm2m'
        self.assertEqual(field_2.dehydrate(bundle_1), [])

        field_3 = ToManyField(SubjectResource, 'subjects')
        field_3.instance_name = 'm2m'
        bundle_3 = Bundle(obj=self.note_1)
        self.assertEqual(field_3.dehydrate(bundle_3), ['/api/v1/subjects/1/', '/api/v1/subjects/2/'])

        field_4 = ToManyField(SubjectResource, 'subjects', full=True)
        field_4.instance_name = 'm2m'
        bundle_4 = Bundle(obj=self.note_1)
        subject_bundle_list = field_4.dehydrate(bundle_4)
        self.assertEqual(len(subject_bundle_list), 2)
        self.assertEqual(isinstance(subject_bundle_list[0], Bundle), True)
        self.assertEqual(subject_bundle_list[0].data['name'], u'News')
        self.assertEqual(subject_bundle_list[0].data['url'], u'/news/')
        self.assertEqual(subject_bundle_list[0].obj.name, u'News')
        self.assertEqual(subject_bundle_list[0].obj.url, u'/news/')
        self.assertEqual(isinstance(subject_bundle_list[1], Bundle), True)
        self.assertEqual(subject_bundle_list[1].data['name'], u'Photos')
        self.assertEqual(subject_bundle_list[1].data['url'], u'/photos/')
        self.assertEqual(subject_bundle_list[1].obj.name, u'Photos')
        self.assertEqual(subject_bundle_list[1].obj.url, u'/photos/')

        field_5 = ToManyField(SubjectResource, 'subjects')
        field_5.instance_name = 'm2m'
        bundle_5 = Bundle(obj=self.note_2)
        self.assertEqual(field_5.dehydrate(bundle_5), ['/api/v1/subjects/1/', '/api/v1/subjects/3/'])

        field_6 = ToManyField(SubjectResource, 'subjects')
        field_6.instance_name = 'm2m'
        bundle_6 = Bundle(obj=self.note_3)
        self.assertEqual(field_6.dehydrate(bundle_6), [])

        try:
            # Regression for missing variable initialization.
            field_7 = ToManyField(SubjectResource, None)
            field_7.instance_name = 'm2m'
            bundle_7 = Bundle(obj=self.note_3)
            field_7.dehydrate(bundle_7)
            self.fail('ToManyField requires an attribute of some type.')
        except ApiFieldError:
            pass

    def test_dehydrate_with_callable(self):
        note = Note()
        bundle_1 = Bundle(obj=self.note_2)
        field_1 = ToManyField(SubjectResource, attribute=lambda bundle: Subject.objects.filter(notes=bundle.obj, name__startswith='Personal'))
        field_1.instance_name = 'm2m'

        self.assertEqual(field_1.dehydrate(bundle_1), ['/api/v1/subjects/3/'])

    def test_hydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)

        # With no value or nullable, we should get an ``ApiFieldError``.
        field_1 = ToManyField(SubjectResource, 'subjects')
        field_1.instance_name = 'm2m'
        self.assertRaises(ApiFieldError, field_1.hydrate_m2m, bundle)

        # The nullable case.
        field_2 = ToManyField(SubjectResource, 'subjects', null=True)
        field_2.instance_name = 'm2m'
        empty_bundle = Bundle()
        self.assertEqual(field_2.hydrate_m2m(empty_bundle), [])

        field_3 = ToManyField(SubjectResource, 'subjects', null=True)
        field_3.instance_name = 'm2m'
        bundle_3 = Bundle(data={'m2m': []})
        self.assertEqual(field_3.hydrate_m2m(bundle_3), [])

        # Wrong resource URI.
        field_4 = ToManyField(SubjectResource, 'subjects')
        field_4.instance_name = 'm2m'
        bundle_4 = Bundle(data={'m2m': ['/api/v1/subjects/abc/']})
        self.assertRaises(NotFound, field_4.hydrate_m2m, bundle_4)

        # A real, live attribute!
        field_5 = ToManyField(SubjectResource, 'subjects')
        field_5.instance_name = 'm2m'
        bundle_5 = Bundle(data={'m2m': ['/api/v1/subjects/1/']})
        subject_bundle_list = field_5.hydrate_m2m(bundle_5)
        self.assertEqual(len(subject_bundle_list), 1)
        self.assertEqual(subject_bundle_list[0].data['name'], u'News')
        self.assertEqual(subject_bundle_list[0].data['url'], u'/news/')
        self.assertEqual(subject_bundle_list[0].obj.name, u'News')
        self.assertEqual(subject_bundle_list[0].obj.url, u'/news/')

        field_6 = ToManyField(SubjectResource, 'subjects')
        field_6.instance_name = 'm2m'
        bundle_6 = Bundle(data={'m2m': [
            {
                'name': u'Foo',
                'url': u'/foo/',
            },
            {
                'name': u'Bar',
                'url': u'/bar/',
            },
        ]})
        subject_bundle_list = field_6.hydrate_m2m(bundle_6)
        self.assertEqual(len(subject_bundle_list), 2)
        self.assertEqual(subject_bundle_list[0].data['name'], u'Foo')
        self.assertEqual(subject_bundle_list[0].data['url'], u'/foo/')
        self.assertEqual(subject_bundle_list[0].obj.name, u'Foo')
        self.assertEqual(subject_bundle_list[0].obj.url, u'/foo/')
        self.assertEqual(subject_bundle_list[1].data['name'], u'Bar')
        self.assertEqual(subject_bundle_list[1].data['url'], u'/bar/')
        self.assertEqual(subject_bundle_list[1].obj.name, u'Bar')
        self.assertEqual(subject_bundle_list[1].obj.url, u'/bar/')

        # The blank case.
        field_7 = ToManyField(SubjectResource, 'fk', blank=True)
        field_7.instance_name = 'fk'
        self.assertEqual(field_7.hydrate(bundle_6), None)

        field_8 = ToManyField(SubjectResource, 'm2m', blank=True)
        field_8.instance_name = 'm2m'
        subject_bundle_list_2 = field_8.hydrate_m2m(bundle_6)
        self.assertEqual(len(subject_bundle_list_2), 2)
        self.assertEqual(subject_bundle_list_2[0].data['name'], u'Foo')
        self.assertEqual(subject_bundle_list_2[0].data['url'], u'/foo/')
        self.assertEqual(subject_bundle_list_2[0].obj.name, u'Foo')
        self.assertEqual(subject_bundle_list_2[0].obj.url, u'/foo/')
        self.assertEqual(subject_bundle_list_2[1].data['name'], u'Bar')
        self.assertEqual(subject_bundle_list_2[1].data['url'], u'/bar/')
        self.assertEqual(subject_bundle_list_2[1].obj.name, u'Bar')
        self.assertEqual(subject_bundle_list_2[1].obj.url, u'/bar/')

        # The readonly case.
        field_9 = ToManyField(SubjectResource, 'subjects', readonly=True)
        field_9.instance_name = 'm2m'
        self.assertEqual(field_9.hydrate(bundle_6), None)
