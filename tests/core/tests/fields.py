import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.exceptions import ApiFieldError, NotFound
from tastypie.fields import *
from tastypie.representations.models import ModelRepresentation
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
        
        field_2 = ApiField(attribute='foo', default=True, null=True, readonly=True)
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(field_2.attribute, 'foo')
        self.assertEqual(field_2._default, True)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.value, None)
        self.assertEqual(field_2.readonly, True)
    
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
        
        # The readonly case.
        field_5 = ApiField(readonly=True)
        field_5.value = 'abcdef'
        self.assertEqual(field_5.hydrate(), None)
        
        # A real, live attribute!
        field_6 = ApiField(attribute='title')
        field_6.value = note.title
        self.assertEqual(field_6.hydrate(), u'First Post!')


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


class UserRepresentation(ModelRepresentation):
    class Meta:
        queryset = User.objects.all()
    
    def get_resource_uri(self):
        return '/api/v1/users/%s/' % self.instance.id


class ForeignKeyTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_init(self):
        field_1 = ForeignKey(UserRepresentation, 'author')
        self.assertEqual(field_1.instance_name, None)
        self.assertEqual(issubclass(field_1.to, UserRepresentation), True)
        self.assertEqual(field_1.attribute, 'author')
        self.assertEqual(field_1.related_name, None)
        self.assertEqual(field_1.null, False)
        self.assertEqual(field_1.full_repr, False)
        self.assertEqual(field_1.value, None)
        
        field_2 = ForeignKey(UserRepresentation, 'author', null=True)
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(issubclass(field_2.to, UserRepresentation), True)
        self.assertEqual(field_2.attribute, 'author')
        self.assertEqual(field_2.related_name, None)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.full_repr, False)
        self.assertEqual(field_2.value, None)
    
    def test_has_default(self):
        field_1 = ForeignKey(UserRepresentation, 'author')
        self.assertEqual(field_1.has_default(), False)
    
    def test_default(self):
        field_1 = ForeignKey(UserRepresentation, 'author')
        
        try:
            # self.assertRaises isn't cooperating here. Do it the hard way.
            field_1.default
            self.fail()
        except ApiFieldError:
            pass
    
    def test_dehydrate(self):
        note = Note()
        field_1 = ForeignKey(UserRepresentation, 'author')
        self.assertRaises(ApiFieldError, field_1.dehydrate, note)
        
        field_2 = ForeignKey(UserRepresentation, 'author', null=True)
        self.assertEqual(field_2.dehydrate(note), None)
        
        note = Note.objects.get(pk=1)
        
        field_3 = ForeignKey(UserRepresentation, 'author')
        self.assertEqual(field_3.dehydrate(note), '/api/v1/users/1/')
        
        field_4 = ForeignKey(UserRepresentation, 'author', full_repr=True)
        user_repr = field_4.dehydrate(note)
        self.assertEqual(isinstance(user_repr, UserRepresentation), True)
        self.assertEqual(user_repr.username.value, u'johndoe')
        self.assertEqual(user_repr.email.value, u'john@doe.com')
    
    def test_hydrate(self):
        note = Note.objects.get(pk=1)
        
        # With no value or nullable, we should get an ``ApiFieldError``.
        field_1 = ForeignKey(UserRepresentation, 'author')
        self.assertRaises(ApiFieldError, field_1.hydrate)
        
        # The nullable case.
        field_2 = ForeignKey(UserRepresentation, 'author', null=True)
        field_2.value = None
        self.assertEqual(field_2.hydrate(), None)
        
        # Wrong resource URI.
        field_3 = ForeignKey(UserRepresentation, 'author')
        field_3.value = '/api/v1/users/abc/'
        self.assertRaises(NotFound, field_3.hydrate)
        
        # A real, live attribute!
        field_4 = ForeignKey(UserRepresentation, 'author')
        field_4.value = '/api/v1/users/1/'
        user_repr = field_4.hydrate()
        self.assertEqual(user_repr.username.value, u'johndoe')
        self.assertEqual(user_repr.email.value, u'john@doe.com')
        
        field_5 = ForeignKey(UserRepresentation, 'author')
        field_5.value = {
            'username': u'mistersmith',
            'email': u'smith@example.com',
            'password': u'foobar',
        }
        user_repr = field_5.hydrate()
        self.assertEqual(user_repr.username.value, u'mistersmith')
        self.assertEqual(user_repr.email.value, u'smith@example.com')


class SubjectRepresentation(ModelRepresentation):
    class Meta:
        queryset = Subject.objects.all()
    
    def get_resource_uri(self):
        return '/api/v1/subjects/%s/' % self.instance.id


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
        field_1 = ManyToManyField(SubjectRepresentation, 'subjects')
        self.assertEqual(field_1.instance_name, None)
        self.assertEqual(issubclass(field_1.to, SubjectRepresentation), True)
        self.assertEqual(field_1.attribute, 'subjects')
        self.assertEqual(field_1.related_name, None)
        self.assertEqual(field_1.null, False)
        self.assertEqual(field_1.full_repr, False)
        self.assertEqual(field_1.value, None)
        
        field_2 = ManyToManyField(SubjectRepresentation, 'subjects', null=True)
        self.assertEqual(field_2.instance_name, None)
        self.assertEqual(issubclass(field_2.to, SubjectRepresentation), True)
        self.assertEqual(field_2.attribute, 'subjects')
        self.assertEqual(field_2.related_name, None)
        self.assertEqual(field_2.null, True)
        self.assertEqual(field_2.full_repr, False)
        self.assertEqual(field_2.value, None)
    
    def test_has_default(self):
        field_1 = ManyToManyField(SubjectRepresentation, 'subjects')
        self.assertEqual(field_1.has_default(), False)
    
    def test_default(self):
        field_1 = ManyToManyField(SubjectRepresentation, 'subjects')
        
        try:
            # self.assertRaises isn't cooperating here. Do it the hard way.
            field_1.default
            self.fail()
        except ApiFieldError:
            pass
    
    def test_dehydrate(self):
        note = Note()
        field_1 = ManyToManyField(SubjectRepresentation, 'subjects')
        
        try:
            # self.assertRaises isn't cooperating here. Do it the hard way.
            field_1.dehydrate(note)
            self.fail()
        except ApiFieldError:
            pass
        
        field_2 = ManyToManyField(SubjectRepresentation, 'subjects', null=True)
        self.assertEqual(field_2.dehydrate(note), [])
        
        field_3 = ManyToManyField(SubjectRepresentation, 'subjects')
        self.assertEqual(field_3.dehydrate(self.note_1), ['/api/v1/subjects/1/', '/api/v1/subjects/2/'])
        
        field_4 = ManyToManyField(SubjectRepresentation, 'subjects', full_repr=True)
        subject_repr_list = field_4.dehydrate(self.note_1)
        self.assertEqual(len(subject_repr_list), 2)
        self.assertEqual(isinstance(subject_repr_list[0], SubjectRepresentation), True)
        self.assertEqual(subject_repr_list[0].name.value, u'News')
        self.assertEqual(subject_repr_list[0].url.value, u'/news/')
        self.assertEqual(isinstance(subject_repr_list[1], SubjectRepresentation), True)
        self.assertEqual(subject_repr_list[1].name.value, u'Photos')
        self.assertEqual(subject_repr_list[1].url.value, u'/photos/')
        
        field_4 = ManyToManyField(SubjectRepresentation, 'subjects')
        self.assertEqual(field_4.dehydrate(self.note_2), ['/api/v1/subjects/1/', '/api/v1/subjects/3/'])
        
        field_5 = ManyToManyField(SubjectRepresentation, 'subjects')
        self.assertEqual(field_5.dehydrate(self.note_3), [])
    
    def test_hydrate(self):
        note = Note.objects.get(pk=1)
        
        # With no value or nullable, we should get an ``ApiFieldError``.
        field_1 = ManyToManyField(SubjectRepresentation, 'subjects')
        self.assertRaises(ApiFieldError, field_1.hydrate_m2m)
        
        # The nullable case.
        field_2 = ManyToManyField(SubjectRepresentation, 'subjects', null=True)
        field_2.value = None
        self.assertEqual(field_2.hydrate_m2m(), None)
        
        field_3 = ManyToManyField(SubjectRepresentation, 'subjects', null=True)
        field_3.value = []
        self.assertEqual(field_3.hydrate_m2m(), [])
        
        # Wrong resource URI.
        field_4 = ManyToManyField(SubjectRepresentation, 'subjects')
        field_4.value = ['/api/v1/subjects/abc/']
        self.assertRaises(NotFound, field_4.hydrate_m2m)
        
        # A real, live attribute!
        field_5 = ManyToManyField(SubjectRepresentation, 'subjects')
        field_5.value = ['/api/v1/subjects/1/']
        subject_repr_list = field_5.hydrate_m2m()
        self.assertEqual(len(subject_repr_list), 1)
        self.assertEqual(subject_repr_list[0].name.value, u'News')
        self.assertEqual(subject_repr_list[0].url.value, u'/news/')
        
        field_6 = ManyToManyField(SubjectRepresentation, 'subjects')
        field_6.value = [
            {
                'name': u'Foo',
                'url': u'/foo/',
            },
            {
                'name': u'Bar',
                'url': u'/bar/',
            },
        ]
        subject_repr_list = field_6.hydrate_m2m()
        self.assertEqual(len(subject_repr_list), 2)
        self.assertEqual(subject_repr_list[0].name.value, u'Foo')
        self.assertEqual(subject_repr_list[0].url.value, u'/foo/')
        self.assertEqual(subject_repr_list[1].name.value, u'Bar')
        self.assertEqual(subject_repr_list[1].url.value, u'/bar/')
