import datetime
from dateutil.tz import *
from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.bundle import Bundle
from tastypie.exceptions import ApiFieldError, NotFound
from tastypie.fields import *
from tastypie.resources import ModelResource
from core.models import Note, Subject


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
        self.assertEqual(field_1.help_text, 'A file path as a string. Ex: "/tmp/photos/my_photo.jpg"')
        
        field_2 = FileField(help_text="Custom.")
        self.assertEqual(field_2.help_text, 'Custom.')
    
    def test_dehydrated_type(self):
        field_1 = FileField()
        self.assertEqual(field_1.dehydrated_type, 'string')
    
    def test_dehydrate(self):
        note = Note.objects.get(pk=1)
        note.image = '/images/foo/bar/clarus.gif'
        bundle = Bundle(obj=note)
        
        field_1 = FileField(attribute='image', default=True)
        self.assertEqual(field_1.dehydrate(bundle), u'http://localhost:8080/media/images/foo/bar/clarus.gif')
        
        field_2 = FileField(default='img/default_avatar.jpg')
        self.assertEqual(field_2.dehydrate(bundle), u'http://localhost:8080/media/img/default_avatar.jpg')
        
        note = Note.objects.get(pk=1)
        note.image = ''
        bundle = Bundle(obj=note)
        
        field_3 = FileField(attribute='image', default=True)
        self.assertEqual(field_3.dehydrate(bundle), u'')
        
        note.image = None
        bundle = Bundle(obj=note)
        
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


class ForeignKeyTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_init(self):
        field_1 = ForeignKey(UserResource, 'author')
        self.assertEqual(field_1.instance_name, None)
        self.assertEqual(issubclass(field_1.to, UserResource), True)
        self.assertEqual(field_1.attribute, 'author')
        self.assertEqual(field_1.related_name, None)
        self.assertEqual(field_1.null, False)
        self.assertEqual(field_1.full, False)
        self.assertEqual(field_1.readonly, False)
        self.assertEqual(field_1.help_text, 'A single related resource. Can be either a URI or set of nested resource data.')
        
        field_2 = ForeignKey(UserResource, 'author', null=True, help_text="Points to a User.")
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(issubclass(field_2.to, UserResource), True)
        self.assertEqual(field_2.attribute, 'author')
        self.assertEqual(field_2.related_name, None)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.full, False)
        self.assertEqual(field_2.readonly, False)
        self.assertEqual(field_2.help_text, 'Points to a User.')
    
    def test_dehydrated_type(self):
        field_1 = ForeignKey(UserResource, 'author')
        self.assertEqual(field_1.dehydrated_type, 'related')
    
    def test_has_default(self):
        field_1 = ForeignKey(UserResource, 'author')
        self.assertEqual(field_1.has_default(), False)
    
    def test_default(self):
        field_1 = ForeignKey(UserResource, 'author')
        
        try:
            # self.assertRaises isn't cooperating here. Do it the hard way.
            field_1.default
            self.fail()
        except ApiFieldError:
            pass
    
    def test_dehydrate(self):
        note = Note()
        bundle = Bundle(obj=note)
        
        field_1 = ForeignKey(UserResource, 'author')
        self.assertRaises(ApiFieldError, field_1.dehydrate, bundle)
        
        field_2 = ForeignKey(UserResource, 'author', null=True)
        self.assertEqual(field_2.dehydrate(bundle), None)
        
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)
        
        field_3 = ForeignKey(UserResource, 'author')
        self.assertEqual(field_3.dehydrate(bundle), '/api/v1/users/1/')
        
        field_4 = ForeignKey(UserResource, 'author', full=True)
        user_bundle = field_4.dehydrate(bundle)
        self.assertEqual(isinstance(user_bundle, Bundle), True)
        self.assertEqual(user_bundle.data['username'], u'johndoe')
        self.assertEqual(user_bundle.data['email'], u'john@doe.com')
    
    def test_hydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)
        
        # With no value or nullable, we should get an ``ApiFieldError``.
        field_1 = ForeignKey(UserResource, 'author')
        self.assertRaises(ApiFieldError, field_1.hydrate, bundle)
        
        # The nullable case.
        field_2 = ForeignKey(UserResource, 'author', null=True)
        field_2.instance_name = 'fk'
        bundle.data['fk'] = None
        self.assertEqual(field_2.hydrate(bundle), None)
        
        # Wrong resource URI.
        field_3 = ForeignKey(UserResource, 'author')
        field_3.instance_name = 'fk'
        bundle.data['fk'] = '/api/v1/users/abc/'
        self.assertRaises(NotFound, field_3.hydrate, bundle)
        
        # A real, live attribute!
        field_4 = ForeignKey(UserResource, 'author')
        field_4.instance_name = 'fk'
        bundle.data['fk'] = '/api/v1/users/1/'
        fk_bundle = field_4.hydrate(bundle)
        self.assertEqual(fk_bundle.data['username'], u'johndoe')
        self.assertEqual(fk_bundle.data['email'], u'john@doe.com')
        self.assertEqual(fk_bundle.obj.username, u'johndoe')
        self.assertEqual(fk_bundle.obj.email, u'john@doe.com')
        
        field_5 = ForeignKey(UserResource, 'author')
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
        field_6 = ForeignKey(UserResource, 'author')
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


class SubjectResource(ModelResource):
    class Meta:
        resource_name = 'subjects'
        queryset = Subject.objects.all()
    
    def get_resource_uri(self, bundle):
        return '/api/v1/subjects/%s/' % bundle.obj.id


class ManyToManyFieldTestCase(TestCase):
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
        field_1 = ManyToManyField(SubjectResource, 'subjects')
        self.assertEqual(field_1.instance_name, None)
        self.assertEqual(issubclass(field_1.to, SubjectResource), True)
        self.assertEqual(field_1.attribute, 'subjects')
        self.assertEqual(field_1.related_name, None)
        self.assertEqual(field_1.null, False)
        self.assertEqual(field_1.full, False)
        self.assertEqual(field_1.readonly, False)
        self.assertEqual(field_1.help_text, 'Many related resources. Can be either a list of URIs or list of individually nested resource data.')
        
        field_2 = ManyToManyField(SubjectResource, 'subjects', null=True, help_text='Points to many Subjects.')
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(issubclass(field_2.to, SubjectResource), True)
        self.assertEqual(field_2.attribute, 'subjects')
        self.assertEqual(field_2.related_name, None)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.full, False)
        self.assertEqual(field_2.readonly, False)
        self.assertEqual(field_2.help_text, 'Points to many Subjects.')
    
    def test_dehydrated_type(self):
        field_1 = ManyToManyField(SubjectResource, 'subjects')
        self.assertEqual(field_1.dehydrated_type, 'related')
    
    def test_has_default(self):
        field_1 = ManyToManyField(SubjectResource, 'subjects')
        self.assertEqual(field_1.has_default(), False)
    
    def test_default(self):
        field_1 = ManyToManyField(SubjectResource, 'subjects')
        
        try:
            # self.assertRaises isn't cooperating here. Do it the hard way.
            field_1.default
            self.fail()
        except ApiFieldError:
            pass
    
    def test_dehydrate(self):
        note = Note()
        bundle_1 = Bundle(obj=note)
        field_1 = ManyToManyField(SubjectResource, 'subjects')
        field_1.instance_name = 'm2m'
        
        try:
            # self.assertRaises isn't cooperating here. Do it the hard way.
            field_1.dehydrate(bundle_1)
            self.fail()
        except ApiFieldError:
            pass
        
        field_2 = ManyToManyField(SubjectResource, 'subjects', null=True)
        field_2.instance_name = 'm2m'
        self.assertEqual(field_2.dehydrate(bundle_1), [])
        
        field_3 = ManyToManyField(SubjectResource, 'subjects')
        field_3.instance_name = 'm2m'
        bundle_3 = Bundle(obj=self.note_1)
        self.assertEqual(field_3.dehydrate(bundle_3), ['/api/v1/subjects/1/', '/api/v1/subjects/2/'])
        
        field_4 = ManyToManyField(SubjectResource, 'subjects', full=True)
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
        
        field_5 = ManyToManyField(SubjectResource, 'subjects')
        field_5.instance_name = 'm2m'
        bundle_5 = Bundle(obj=self.note_2)
        self.assertEqual(field_5.dehydrate(bundle_5), ['/api/v1/subjects/1/', '/api/v1/subjects/3/'])
        
        field_6 = ManyToManyField(SubjectResource, 'subjects')
        field_6.instance_name = 'm2m'
        bundle_6 = Bundle(obj=self.note_3)
        self.assertEqual(field_6.dehydrate(bundle_6), [])
    
    def test_hydrate(self):
        note = Note.objects.get(pk=1)
        bundle = Bundle(obj=note)
        
        # With no value or nullable, we should get an ``ApiFieldError``.
        field_1 = ManyToManyField(SubjectResource, 'subjects')
        field_1.instance_name = 'm2m'
        self.assertRaises(ApiFieldError, field_1.hydrate_m2m, bundle)
        
        # The nullable case.
        field_2 = ManyToManyField(SubjectResource, 'subjects', null=True)
        field_2.instance_name = 'm2m'
        empty_bundle = Bundle()
        self.assertEqual(field_2.hydrate_m2m(empty_bundle), [])
        
        field_3 = ManyToManyField(SubjectResource, 'subjects', null=True)
        field_3.instance_name = 'm2m'
        bundle_3 = Bundle(data={'m2m': []})
        self.assertEqual(field_3.hydrate_m2m(bundle_3), [])
        
        # Wrong resource URI.
        field_4 = ManyToManyField(SubjectResource, 'subjects')
        field_4.instance_name = 'm2m'
        bundle_4 = Bundle(data={'m2m': ['/api/v1/subjects/abc/']})
        self.assertRaises(NotFound, field_4.hydrate_m2m, bundle_4)
        
        # A real, live attribute!
        field_5 = ManyToManyField(SubjectResource, 'subjects')
        field_5.instance_name = 'm2m'
        bundle_5 = Bundle(data={'m2m': ['/api/v1/subjects/1/']})
        subject_bundle_list = field_5.hydrate_m2m(bundle_5)
        self.assertEqual(len(subject_bundle_list), 1)
        self.assertEqual(subject_bundle_list[0].data['name'], u'News')
        self.assertEqual(subject_bundle_list[0].data['url'], u'/news/')
        self.assertEqual(subject_bundle_list[0].obj.name, u'News')
        self.assertEqual(subject_bundle_list[0].obj.url, u'/news/')
        
        field_6 = ManyToManyField(SubjectResource, 'subjects')
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
