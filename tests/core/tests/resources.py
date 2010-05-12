import base64
import datetime
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest, QueryDict
from django.test import TestCase
from tastypie.authentication import BasicAuthentication
from tastypie.bundle import Bundle
from tastypie.exceptions import InvalidFilterError
from tastypie import fields
from tastypie.resources import Resource, ModelResource
from tastypie.serializers import Serializer
from tastypie.throttle import CacheThrottle
from core.models import Note, Subject
try:
    set
except NameError:
    from sets import Set as set


class CustomSerializer(Serializer):
    pass


class TestObject(object):
    name = None
    view_count = None
    date_joined = None


class BasicResource(Resource):
    name = fields.CharField(attribute='name')
    view_count = fields.IntegerField(attribute='view_count', default=0)
    date_joined = fields.DateTimeField(null=True)
    
    class Meta:
        object_class = TestObject
        resource_name = 'basic'
    
    def dehydrate_date_joined(self, bundle):
        if getattr(bundle.obj, 'date_joined', None) is not None:
            return bundle.obj.date_joined
        
        if bundle.data.get('date_joined') is not None:
            return bundle.data.get('date_joined')
        
        return datetime.datetime(2010, 3, 27, 22, 30, 0)
    
    def hydrate_date_joined(self, bundle):
        bundle.obj.date_joined = bundle.data['date_joined']
        return bundle


class AnotherBasicResource(BasicResource):
    name = fields.CharField(attribute='name')
    view_count = fields.IntegerField(attribute='view_count', default=0)
    date_joined = fields.DateField(attribute='created')
    is_active = fields.BooleanField(attribute='is_active', default=True)
    
    class Meta:
        resource_name = 'anotherbasic'


class NoUriBasicResource(BasicResource):
    name = fields.CharField(attribute='name')
    view_count = fields.IntegerField(attribute='view_count', default=0)
    date_joined = fields.DateTimeField(null=True)
    
    class Meta:
        object_class = TestObject
        include_resource_uri = False
        resource_name = 'nouribasic'


class ResourceTestCase(TestCase):
    def test_fields(self):
        basic = BasicResource()
        self.assertEqual(len(basic.fields), 4)
        self.assert_('name' in basic.fields)
        self.assertEqual(isinstance(basic.fields['name'], fields.CharField), True)
        self.assert_('view_count' in basic.fields)
        self.assertEqual(isinstance(basic.fields['view_count'], fields.IntegerField), True)
        self.assert_('date_joined' in basic.fields)
        self.assertEqual(isinstance(basic.fields['date_joined'], fields.DateTimeField), True)
        self.assert_('resource_uri' in basic.fields)
        self.assertEqual(isinstance(basic.fields['resource_uri'], fields.CharField), True)
        
        another = AnotherBasicResource()
        self.assertEqual(len(another.fields), 5)
        self.assert_('name' in another.fields)
        self.assertEqual(isinstance(another.name, fields.CharField), True)
        self.assert_('view_count' in another.fields)
        self.assertEqual(isinstance(another.view_count, fields.IntegerField), True)
        self.assert_('date_joined' in another.fields)
        self.assertEqual(isinstance(another.date_joined, fields.DateField), True)
        self.assert_('is_active' in another.fields)
        self.assertEqual(isinstance(another.is_active, fields.BooleanField), True)
        self.assert_('resource_uri' in basic.fields)
        self.assertEqual(isinstance(basic.resource_uri, fields.CharField), True)
        
        basic = NoUriBasicResource()
        self.assertEqual(len(basic.fields), 3)
        self.assert_('name' in basic.fields)
        self.assertEqual(isinstance(basic.name, fields.CharField), True)
        self.assert_('view_count' in basic.fields)
        self.assertEqual(isinstance(basic.view_count, fields.IntegerField), True)
        self.assert_('date_joined' in basic.fields)
        self.assertEqual(isinstance(basic.date_joined, fields.DateTimeField), True)
    
    def test_full_dehydrate(self):
        test_object_1 = TestObject()
        test_object_1.name = 'Daniel'
        test_object_1.view_count = 12
        test_object_1.date_joined = datetime.datetime(2010, 3, 30, 9, 0, 0)
        test_object_1.foo = "Hi, I'm ignored."
        
        basic = BasicResource()
        
        # Sanity check.
        self.assertEqual(basic.name.value, None)
        self.assertEqual(basic.view_count.value, None)
        self.assertEqual(basic.date_joined.value, None)
        
        bundle_1 = basic.full_dehydrate(test_object_1)
        self.assertEqual(bundle_1.data['name'], 'Daniel')
        self.assertEqual(bundle_1.data['view_count'], 12)
        self.assertEqual(bundle_1.data['date_joined'].year, 2010)
        self.assertEqual(bundle_1.data['date_joined'].day, 30)
        
        # Now check the fallback behaviors.
        test_object_2 = TestObject()
        test_object_2.name = 'Daniel'
        basic_2 = BasicResource()
        
        bundle_2 = basic_2.full_dehydrate(test_object_2)
        self.assertEqual(bundle_2.data['name'], 'Daniel')
        self.assertEqual(bundle_2.data['view_count'], 0)
        self.assertEqual(bundle_2.data['date_joined'].year, 2010)
        self.assertEqual(bundle_2.data['date_joined'].day, 27)
        
        test_object_3 = TestObject()
        test_object_3.name = 'Joe'
        test_object_3.view_count = 5
        test_object_3.created = datetime.datetime(2010, 3, 29, 11, 0, 0)
        test_object_3.is_active = False
        another_1 = AnotherBasicResource()
        
        another_bundle_1 = another_1.full_dehydrate(test_object_3)
        self.assertEqual(another_bundle_1.data['name'], 'Joe')
        self.assertEqual(another_bundle_1.data['view_count'], 5)
        self.assertEqual(another_bundle_1.data['date_joined'].year, 2010)
        self.assertEqual(another_bundle_1.data['date_joined'].day, 29)
        self.assertEqual(another_bundle_1.data['is_active'], False)
    
    def test_full_hydrate(self):
        basic = BasicResource()
        basic_bundle_1 = Bundle(data={
            'name': 'Daniel',
            'view_count': 6,
            'date_joined': datetime.datetime(2010, 2, 15, 12, 0, 0)
        })
        
        # Now load up the data.
        hydrated = basic.full_hydrate(basic_bundle_1)
        
        self.assertEqual(hydrated.data['name'], 'Daniel')
        self.assertEqual(hydrated.data['view_count'], 6)
        self.assertEqual(hydrated.data['date_joined'], datetime.datetime(2010, 2, 15, 12, 0, 0))
        self.assertEqual(hydrated.obj.name, 'Daniel')
        self.assertEqual(hydrated.obj.view_count, 6)
        self.assertEqual(hydrated.obj.date_joined, datetime.datetime(2010, 2, 15, 12, 0, 0))
    
    def test_obj_get_list(self):
        basic = BasicResource()
        self.assertRaises(NotImplementedError, basic.obj_get_list)
    
    def test_obj_delete_list(self):
        basic = BasicResource()
        self.assertRaises(NotImplementedError, basic.obj_delete_list)
    
    def test_obj_get(self):
        basic = BasicResource()
        self.assertRaises(NotImplementedError, basic.obj_get, obj_id=1)
    
    def test_obj_create(self):
        basic = BasicResource()
        bundle = Bundle()
        self.assertRaises(NotImplementedError, basic.obj_create, bundle)
    
    def test_obj_update(self):
        basic = BasicResource()
        bundle = Bundle()
        self.assertRaises(NotImplementedError, basic.obj_update, bundle)
    
    def test_obj_delete(self):
        basic = BasicResource()
        self.assertRaises(NotImplementedError, basic.obj_delete)
    
    def test_build_schema(self):
        basic = BasicResource()
        self.assertEqual(basic.build_schema(), {
            'view_count': {
                'readonly': False,
                'type': 'integer',
                'nullable': False
            },
            'date_joined': {
                'readonly': False,
                'type': 'datetime',
                'nullable': True
            },
            'name': {
                'readonly': False,
                'type': 'string',
                'nullable': False
            },
            'resource_uri': {
                'readonly': True,
                'type': 'string',
                'nullable': False
            }
        })


# ====================
# Model-based tests...
# ====================


class NoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        filtering = {
            'content': ['startswith', 'exact'],
            'title': 'all',
            'slug': ['exact'],
        }
        queryset = Note.objects.filter(is_active=True)
    
    def get_resource_uri(self, bundle_or_obj):
        return '/api/v1/notes/%s/' % bundle_or_obj.obj.id


# FIXME: Note that subclassing is currently broken.
class LightlyCustomNoteResource(NoteResource):
    class Meta:
        resource_name = 'noteish'
        allowed_methods = ['get']
        queryset = Note.objects.filter(is_active=True)


class VeryCustomNoteResource(NoteResource):
    author = fields.CharField(attribute='author__username')
    constant = fields.IntegerField(default=20)
    
    class Meta:
        limit = 50
        resource_name = 'notey'
        serializer = CustomSerializer()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'post', 'put']
        queryset = Note.objects.all()
        fields = ['title', 'content', 'created', 'is_active']


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
    
    def get_resource_uri(self, bundle_or_obj):
        return '/api/v1/users/%s/' % bundle_or_obj.obj.id


class DetailedNoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'author')
    hello_world = fields.CharField(default='world')
    
    class Meta:
        resource_name = 'detailednotes'
        filtering = {
            'content': ['startswith', 'exact'],
            'title': 'all',
            'slug': ['exact'],
            'user': ['gt', 'gte', 'lt', 'lte', 'exact'],
            'hello_world': ['exact'], # Note this is invalid for filtering.
        }
        queryset = Note.objects.filter(is_active=True)
    
    def get_resource_uri(self, bundle_or_obj):
        return '/api/v1/notes/%s/' % bundle_or_obj.obj.id


class ThrottledNoteResource(NoteResource):
    class Meta:
        resource_name = 'throttlednotes'
        queryset = Note.objects.filter(is_active=True)
        throttle = CacheThrottle(throttle_at=2, timeframe=5, expiration=5)


class BasicAuthNoteResource(NoteResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)
        authentication = BasicAuthentication()


class NoUriNoteResource(ModelResource):
    class Meta:
        queryset = Note.objects.filter(is_active=True)
        include_resource_uri = False
        resource_name = 'nourinote'


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'users'


class SubjectResource(ModelResource):
    class Meta:
        queryset = Subject.objects.all()
        resource_name = 'subjects'


class RelatedNoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author')
    subjects = fields.ManyToManyField(SubjectResource, 'subjects')
    
    class Meta:
        queryset = Note.objects.all()
        resource_name = 'relatednotes'
        fields = ['title', 'slug', 'content', 'created', 'is_active']


class ModelResourceTestCase(TestCase):
    fixtures = ['note_testdata.json']
    urls = 'core.tests.field_urls'
    
    def setUp(self):
        super(ModelResourceTestCase, self).setUp()
        self.note_1 = Note.objects.get(pk=1)
        self.subject_1 = Subject.objects.create(
            name='News',
            url='/news/'
        )
        self.subject_2 = Subject.objects.create(
            name='Photos',
            url='/photos/'
        )
        self.note_1.subjects.add(self.subject_1)
        self.note_1.subjects.add(self.subject_2)
    
    def test_init(self):
        # Very minimal & stock.
        resource_1 = NoteResource()
        self.assertEqual(len(resource_1.fields), 7)
        self.assertNotEqual(resource_1._meta.queryset, None)
        self.assertEqual(resource_1._meta.resource_name, 'notes')
        self.assertEqual(resource_1._meta.limit, 20)
        self.assertEqual(resource_1._meta.list_allowed_methods, ['get', 'post', 'put', 'delete'])
        self.assertEqual(resource_1._meta.detail_allowed_methods, ['get', 'post', 'put', 'delete'])
        self.assertEqual(isinstance(resource_1._meta.serializer, Serializer), True)
        self.assertEqual(resource_1._meta.available_filters, set(['title__lte', 'title__isnull', 'slug__exact', 'title__istartswith', 'title__icontains', 'content__startswith', 'title__range', 'title__endswith', 'title__iexact', 'title__day', 'title__lt', 'content', 'title__contains', 'title__year', 'title__iregex', 'title', 'title__month', 'title__gt', 'title__week_day', 'slug', 'title__gte', 'title__regex', 'title__iendswith', 'content__exact', 'title__in', 'title__exact', 'title__search', 'title__startswith']))
        
        # Lightly custom.
        resource_2 = LightlyCustomNoteResource()
        self.assertEqual(len(resource_2.fields), 7)
        self.assertNotEqual(resource_2._meta.queryset, None)
        self.assertEqual(resource_2._meta.resource_name, 'noteish')
        self.assertEqual(resource_2._meta.limit, 20)
        self.assertEqual(resource_2._meta.list_allowed_methods, ['get'])
        self.assertEqual(resource_2._meta.detail_allowed_methods, ['get'])
        self.assertEqual(isinstance(resource_2._meta.serializer, Serializer), True)
        
        # Highly custom.
        resource_3 = VeryCustomNoteResource()
        self.assertEqual(len(resource_3.fields), 7)
        self.assertNotEqual(resource_3._meta.queryset, None)
        self.assertEqual(resource_3._meta.resource_name, 'notey')
        self.assertEqual(resource_3._meta.limit, 50)
        self.assertEqual(resource_3._meta.list_allowed_methods, ['get'])
        self.assertEqual(resource_3._meta.detail_allowed_methods, ['get', 'post', 'put'])
        self.assertEqual(isinstance(resource_3._meta.serializer, CustomSerializer), True)
    
    def test_urls(self):
        # The common case, where the ``Api`` specifies the name.
        resource = NoteResource(api_name='v1')
        patterns = resource.urls
        self.assertEqual(len(patterns), 4)
        self.assertEqual([pattern.name for pattern in patterns], ['api_dispatch_list', 'api_get_schema', 'api_get_multiple', 'api_dispatch_detail'])
        self.assertEqual(reverse('api_dispatch_list', kwargs={
            'api_name': 'v1',
            'resource_name': 'notes',
        }), '/api/v1/notes/')
        self.assertEqual(reverse('api_dispatch_detail', kwargs={
            'api_name': 'v1',
            'resource_name': 'notes',
            'obj_id': 1,
        }), '/api/v1/notes/1/')
        
        # Start over.
        resource = NoteResource()
        patterns = resource.urls
        self.assertEqual(len(patterns), 4)
        self.assertEqual([pattern.name for pattern in patterns], ['api_dispatch_list', 'api_get_schema', 'api_get_multiple', 'api_dispatch_detail'])
        self.assertEqual(reverse('api_dispatch_list', urlconf='core.tests.manual_urls', kwargs={
            'resource_name': 'notes',
        }), '/notes/')
        self.assertEqual(reverse('api_dispatch_detail', urlconf='core.tests.manual_urls', kwargs={
            'resource_name': 'notes',
            'obj_id': 1,
        }), '/notes/1/')
    
    def test_determine_format(self):
        resource = NoteResource()
        request = HttpRequest()
        
        # Default.
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        # Test forcing the ``format`` parameter.
        request.GET = {'format': 'json'}
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        request.GET = {'format': 'jsonp'}
        self.assertEqual(resource.determine_format(request), 'text/javascript')
        
        request.GET = {'format': 'xml'}
        self.assertEqual(resource.determine_format(request), 'application/xml')
        
        request.GET = {'format': 'yaml'}
        self.assertEqual(resource.determine_format(request), 'text/yaml')
        
        request.GET = {'format': 'foo'}
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        # Test the ``Accept`` header.
        request.META = {'HTTP_ACCEPT': 'application/json'}
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        self.assertEqual(resource.determine_format(request), 'text/javascript')
        
        request.META = {'HTTP_ACCEPT': 'application/xml'}
        self.assertEqual(resource.determine_format(request), 'application/xml')
        
        request.META = {'HTTP_ACCEPT': 'text/yaml'}
        self.assertEqual(resource.determine_format(request), 'text/yaml')
        
        request.META = {'HTTP_ACCEPT': 'text/html'}
        self.assertEqual(resource.determine_format(request), 'text/html')
        
        request.META = {'HTTP_ACCEPT': 'application/json,application/xml;q=0.9,*/*;q=0.8'}
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        request.META = {'HTTP_ACCEPT': 'text/plain,application/xml,application/json;q=0.9,*/*;q=0.8'}
        self.assertEqual(resource.determine_format(request), 'application/xml')
    
    def test__get_available_filters(self):
        resource = NoteResource()
        
        # Field not in the resource.
        borked_filters_1 = {
            'foobar': 'all',
        }
        self.assertRaises(InvalidFilterError, resource._get_available_filters, borked_filters_1)
        
        # Invalid shortcut.
        borked_filters_2 = {
            'title': 'foobar',
        }
        self.assertRaises(InvalidFilterError, resource._get_available_filters, borked_filters_2)
        
        # Invalid filter types.
        borked_filters_3 = {
            'title': ['exact', 'barf'],
        }
        self.assertRaises(InvalidFilterError, resource._get_available_filters, borked_filters_3)
        
        # Valid none.
        filters_1 = {}
        self.assertEqual(resource._get_available_filters(filters_1), set())
        
        # Valid single.
        filters_2 = {
            'title': ['startswith'],
        }
        self.assertEqual(resource._get_available_filters(filters_2), set(['title__startswith']))
        
        # Valid multiple.
        filters_3 = {
            'title': ['startswith', 'contains', 'endswith'],
        }
        self.assertEqual(resource._get_available_filters(filters_3), set(['title__contains', 'title__endswith', 'title__startswith']))
        
        # Valid all.
        filters_4 = {
            'title': 'all',
        }
        self.assertEqual(resource._get_available_filters(filters_4), set(set(['title__lte', 'title__isnull', 'title__week_day', 'title__icontains', 'title__range', 'title__endswith', 'title__iexact', 'title__day', 'title__lt', 'title__contains', 'title__year', 'title__iregex', 'title', 'title__month', 'title__gt', 'title__istartswith', 'title__gte', 'title__regex', 'title__iendswith', 'title__in', 'title__exact', 'title__search', 'title__startswith'])))
        
        # Valid variety.
        filters_5 = {
            'title': 'all',
            'content': ['endswith'],
        }
        self.assertEqual(resource._get_available_filters(filters_5), set(['title__lte', 'title__isnull', 'title__week_day', 'title__icontains', 'title__range', 'title__endswith', 'title__iexact', 'title__day', 'title__lt', 'title__contains', 'title__year', 'title__iregex', 'title', 'title__month', 'title__gt', 'title__istartswith', 'title__gte', 'title__regex', 'title__iendswith', 'content__endswith', 'title__in', 'title__exact', 'title__search', 'title__startswith']))
        
        # Valid relation.
        resource_2 = DetailedNoteResource()
        filters_6 = {
            'content': ['endswith'],
            'user': ['gt', 'gte', 'exact'],
        }
        self.assertEqual(resource_2._get_available_filters(filters_6), set(['user__gt', 'user__exact', 'user', 'content__endswith', 'user__gte']))
    
    def test_build_filters(self):
        resource = NoteResource()
        
        # Valid none.
        self.assertEqual(resource.build_filters(), {})
        self.assertEqual(resource.build_filters(filters=None), {})
        
        # No available attribute.
        self.assertEqual(resource.build_filters(filters={'resource_url__exact': '/foo/bar/'}), {})
        
        # Filter valid but disallowed.
        self.assertEqual(resource.build_filters(filters={'slug__startswith': 'whee'}), {})
        
        # Skipped due to not being recognized.
        self.assertEqual(resource.build_filters(filters={'moof__exact': 'baz'}), {})
        
        # Valid simple (implicit ``__exact``).
        self.assertEqual(resource.build_filters(filters={'title': 'Hello world.'}), {'title__exact': 'Hello world.'})
        
        # Valid simple (explicit ``__exact``).
        self.assertEqual(resource.build_filters(filters={'title__exact': 'Hello world.'}), {'title__exact': 'Hello world.'})
        
        # Valid simple (non-``__exact``).
        self.assertEqual(resource.build_filters(filters={'content__startswith': 'Hello'}), {'content__startswith': 'Hello'})
        
        # Valid multiple.
        self.assertEqual(resource.build_filters(filters={
            'slug__exact': 'Hello',
            'title': 'RAGE',
            'content__startswith': 'A thing here.'
        }), {'slug__exact': 'Hello', 'content__startswith': 'A thing here.', 'title__exact': 'RAGE'})
        
        # Valid multiple (model attribute differs from field name).
        resource_2 = DetailedNoteResource()
        filters_1 = {
            'slug__exact': 'Hello',
            'title': 'RAGE',
            'content__startswith': 'A thing here.',
            'user__gt': 2,
        }
        self.assertEqual(resource_2.build_filters(filters=filters_1), {'title__exact': 'RAGE', 'slug__exact': 'Hello', 'author__gt': 2, 'content__startswith': 'A thing here.'})
        
        # No relationship traversal to the filter, please.
        self.assertEqual(resource_2.build_filters(filters={'hello_world__foo__exact': 'baz'}), {})
    
    def test_get_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 4}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "Thu, 1 Apr 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "Thu, 1 Apr 2010 20:05:00 -0500"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "Fri, 2 Apr 2010 10:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "Fri, 2 Apr 2010 10:05:00 -0500"}]}')
        
        # Test slicing.
        # First an invalid offset.
        request.GET = {'format': 'json', 'offset': 'abc', 'limit': 1}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 400)
        
        # Then an out of range offset.
        request.GET = {'format': 'json', 'offset': -1, 'limit': 1}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 400)
        
        # Then an out of range limit.
        request.GET = {'format': 'json', 'offset': 0, 'limit': -1}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 400)
        
        # Valid slice.
        request.GET = {'format': 'json', 'offset': 0, 'limit': 2}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"meta": {"limit": 2, "next": null, "offset": 0, "previous": null, "total_count": 4}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}]}')
        
        # Valid, slightly overlapping slice.
        request.GET = {'format': 'json', 'offset': 1, 'limit': 2}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"meta": {"limit": 2, "next": null, "offset": 1, "previous": null, "total_count": 4}, "objects": [{"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "Thu, 1 Apr 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "Thu, 1 Apr 2010 20:05:00 -0500"}]}')
        
        # Valid, non-overlapping slice.
        request.GET = {'format': 'json', 'offset': 3, 'limit': 2}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"meta": {"limit": 2, "next": null, "offset": 3, "previous": null, "total_count": 4}, "objects": [{"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "Fri, 2 Apr 2010 10:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "Fri, 2 Apr 2010 10:05:00 -0500"}]}')
        
        # Valid, but beyond the bounds slice.
        request.GET = {'format': 'json', 'offset': 100, 'limit': 2}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"meta": {"limit": 2, "next": null, "offset": 100, "previous": null, "total_count": 4}, "objects": []}')
    
    def test_get_detail(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        
        resp = resource.get_detail(request, obj_id=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}')
        
        resp = resource.get_detail(request, obj_id=2)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}')
        
        resp = resource.get_detail(request, obj_id=300)
        self.assertEqual(resp.status_code, 410)
    
    def test_put_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        
        self.assertEqual(Note.objects.count(), 6)
        request.raw_post_data = '{"objects": [{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back-again", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}]}'
        
        resp = resource.put_list(request)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Note.objects.count(), 3)
        self.assertEqual(Note.objects.filter(is_active=True).count(), 1)
        new_note = Note.objects.get(slug='cat-is-back-again')
        self.assertEqual(new_note.content, "The cat is back. The dog coughed him up out back.")
    
    def test_put_detail(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.raw_post_data = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}'
        
        resp = resource.put_detail(request, obj_id=10)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='cat-is-back')
        self.assertEqual(new_note.content, "The cat is back. The dog coughed him up out back.")
        
        request.raw_post_data = '{"content": "The cat is gone again. I think it was the rabbits that ate him this time.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Gone", "updated": "2010-04-03 20:05:00"}'
        
        resp = resource.put_detail(request, obj_id=10)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='cat-is-back')
        self.assertEqual(new_note.content, u'The cat is gone again. I think it was the rabbits that ate him this time.')
    
    def test_post_list(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}'
        
        resp = resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='cat-is-back')
        self.assertEqual(new_note.content, "The cat is back. The dog coughed him up out back.")
    
    def test_post_detail(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        
        resp = resource.post_detail(request, obj_id=2)
        self.assertEqual(resp.status_code, 501)
    
    def test_delete_list(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'DELETE'
        
        resp = resource.delete_list(request)
        self.assertEqual(resp.status_code, 204)
        # Only the non-actives are left alive.
        self.assertEqual(Note.objects.count(), 2)
    
    def test_delete_detail(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'DELETE'
        
        resp = resource.delete_detail(request, obj_id=2)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Note.objects.count(), 5)
    
    def test_dispatch_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.dispatch_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 4}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "Thu, 1 Apr 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "Thu, 1 Apr 2010 20:05:00 -0500"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "Fri, 2 Apr 2010 10:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "Fri, 2 Apr 2010 10:05:00 -0500"}]}')
    
    def test_dispatch_detail(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.dispatch_detail(request, obj_id=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}')
    
    def test_dispatch(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 4}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "Thu, 1 Apr 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "Thu, 1 Apr 2010 20:05:00 -0500"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "Fri, 2 Apr 2010 10:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "Fri, 2 Apr 2010 10:05:00 -0500"}]}')
        
        resp = resource.dispatch('detail', request, obj_id=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}')
    
    def test_build_bundle(self):
        resource = NoteResource()
        
        unpopulated_bundle = resource.build_bundle()
        self.assertTrue(isinstance(unpopulated_bundle, Bundle))
        self.assertEqual(unpopulated_bundle.data, {})
        
        populated_bundle = resource.build_bundle(data={'title': 'Foo'})
        self.assertTrue(isinstance(populated_bundle, Bundle))
        self.assertEqual(populated_bundle.data, {'title': 'Foo'})
    
    def test_obj_get_list(self):
        resource = NoteResource()
        
        object_list = resource.obj_get_list()
        self.assertEqual(len(object_list), 4)
        self.assertEqual(object_list[0].title, u'First Post!')
        
        notes = NoteResource().obj_get_list()
        self.assertEqual(len(notes), 4)
        self.assertEqual(notes[0].is_active, True)
        self.assertEqual(notes[0].title, u'First Post!')
        self.assertEqual(notes[1].is_active, True)
        self.assertEqual(notes[1].title, u'Another Post')
        self.assertEqual(notes[2].is_active, True)
        self.assertEqual(notes[2].title, u'Recent Volcanic Activity.')
        self.assertEqual(notes[3].is_active, True)
        self.assertEqual(notes[3].title, u"Granny's Gone")
        
        customs = VeryCustomNoteResource().obj_get_list()
        self.assertEqual(len(customs), 6)
        self.assertEqual(customs[0].is_active, True)
        self.assertEqual(customs[0].title, u'First Post!')
        self.assertEqual(customs[0].author.username, u'johndoe')
        self.assertEqual(customs[1].is_active, True)
        self.assertEqual(customs[1].title, u'Another Post')
        self.assertEqual(customs[1].author.username, u'johndoe')
        self.assertEqual(customs[2].is_active, False)
        self.assertEqual(customs[2].title, u'Hello World!')
        self.assertEqual(customs[2].author.username, u'janedoe')
        self.assertEqual(customs[3].is_active, True)
        self.assertEqual(customs[3].title, u'Recent Volcanic Activity.')
        self.assertEqual(customs[3].author.username, u'janedoe')
        self.assertEqual(customs[4].is_active, False)
        self.assertEqual(customs[4].title, u'My favorite new show')
        self.assertEqual(customs[4].author.username, u'johndoe')
        self.assertEqual(customs[5].is_active, True)
        self.assertEqual(customs[5].title, u"Granny's Gone")
        self.assertEqual(customs[5].author.username, u'janedoe')
    
    def test_obj_get(self):
        resource = NoteResource()
        
        obj = resource.obj_get(obj_id=1)
        self.assertTrue(isinstance(obj, Note))
        self.assertEqual(obj.title, u'First Post!')
        
        note = NoteResource()
        note_obj = note.obj_get(obj_id=1)
        self.assertEqual(note_obj.content, u'This is my very first post using my shiny new API. Pretty sweet, huh?')
        self.assertEqual(note_obj.created, datetime.datetime(2010, 3, 30, 20, 5))
        self.assertEqual(note_obj.is_active, True)
        self.assertEqual(note_obj.slug, u'first-post')
        self.assertEqual(note_obj.title, u'First Post!')
        self.assertEqual(note_obj.updated, datetime.datetime(2010, 3, 30, 20, 5))
        
        custom = VeryCustomNoteResource()
        custom_obj = custom.obj_get(obj_id=1)
        self.assertEqual(custom_obj.content, u'This is my very first post using my shiny new API. Pretty sweet, huh?')
        self.assertEqual(custom_obj.created, datetime.datetime(2010, 3, 30, 20, 5))
        self.assertEqual(custom_obj.is_active, True)
        self.assertEqual(custom_obj.author.username, u'johndoe')
        self.assertEqual(custom_obj.title, u'First Post!')
        
        related = RelatedNoteResource()
        related_obj = related.obj_get(obj_id=1)
        self.assertEqual(related_obj.content, u'This is my very first post using my shiny new API. Pretty sweet, huh?')
        self.assertEqual(related_obj.created, datetime.datetime(2010, 3, 30, 20, 5))
        self.assertEqual(related_obj.is_active, True)
        self.assertEqual(related_obj.author.username, u'johndoe')
        self.assertEqual(related_obj.title, u'First Post!')
        self.assertEqual(list(related_obj.subjects.values_list('id', flat=True)), [1, 2])

    def test_jsonp_validation(self):
        resource = NoteResource()

        # invalid JSONP callback should return Http400
        request = HttpRequest()
        request.GET = {'format': 'jsonp', 'callback': '()'}
        request.method = 'GET'
        resp = resource.dispatch_detail(request, obj_id=1)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, 'JSONP callback name is invalid.')

        # valid JSONP callback should work
        request = HttpRequest()
        request.GET = {'format': 'jsonp', 'callback': 'myCallback'}
        request.method = 'GET'
        resp = resource.dispatch_detail(request, obj_id=1)
        self.assertEqual(resp.status_code, 200)
    
    def test_get_schema(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.get_schema(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"content": {"nullable": false, "readonly": false, "type": "string"}, "created": {"nullable": false, "readonly": false, "type": "datetime"}, "is_active": {"nullable": false, "readonly": false, "type": "boolean"}, "resource_uri": {"nullable": false, "readonly": true, "type": "string"}, "slug": {"nullable": false, "readonly": false, "type": "string"}, "title": {"nullable": false, "readonly": false, "type": "string"}, "updated": {"nullable": false, "readonly": false, "type": "datetime"}}')
    
    def test_get_multiple(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.get_multiple(request, id_list='1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}]}')
        
        resp = resource.get_multiple(request, id_list='1;2')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}]}')
        
        resp = resource.get_multiple(request, id_list='2;3')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"not_found": ["3"], "objects": [{"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}]}')
        
        resp = resource.get_multiple(request, id_list='1;2;4;6')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "Thu, 1 Apr 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "Thu, 1 Apr 2010 20:05:00 -0500"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "Fri, 2 Apr 2010 10:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "Fri, 2 Apr 2010 10:05:00 -0500"}]}')
    
    def test_check_throttling(self):
        resource = ThrottledNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 1)
        
        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)
        
        # Throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)
        
        # Throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)
    
    def test_generate_cache_key(self):
        resource = NoteResource()
        self.assertEqual(resource.generate_cache_key(), 'None:notes::')
        self.assertEqual(resource.generate_cache_key('abc', '123'), 'None:notes:abc:123:')
        self.assertEqual(resource.generate_cache_key(foo='bar', moof='baz'), 'None:notes::foo=bar:moof=baz')
        self.assertEqual(resource.generate_cache_key('abc', '123', foo='bar', moof='baz'), 'None:notes:abc:123:foo=bar:moof=baz')
    
    def test_cached_fetch_list(self):
        resource = NoteResource()
        
        object_list = resource.cached_obj_get_list()
        self.assertEqual(len(object_list), 4)
        self.assertEqual(object_list[0].title, u'First Post!')
    
    def test_cached_fetch_detail(self):
        resource = NoteResource()
        
        obj = resource.cached_obj_get(obj_id=1)
        self.assertTrue(isinstance(obj, Note))
        self.assertEqual(obj.title, u'First Post!')
    
    def test_configuration(self):
        note = NoteResource()
        self.assertEqual(len(note.fields), 7)
        self.assertEqual(sorted(note.fields.keys()), ['content', 'created', 'is_active', 'resource_uri', 'slug', 'title', 'updated'])
        self.assertEqual(note.fields['content'].default, '')
        
        custom = VeryCustomNoteResource()
        self.assertEqual(len(custom.fields), 7)
        self.assertEqual(sorted(custom.fields.keys()), ['author', 'constant', 'content', 'created', 'is_active', 'resource_uri', 'title'])
        
        no_uri = NoUriNoteResource()
        self.assertEqual(len(no_uri.fields), 6)
        self.assertEqual(sorted(no_uri.fields.keys()), ['content', 'created', 'is_active', 'slug', 'title', 'updated'])
    
    def test_obj_delete_list_custom_qs(self):
        self.assertEqual(len(Note.objects.all()), 6)
        notes = NoteResource().obj_delete_list()
        self.assertEqual(len(Note.objects.all()), 2)
        
    def test_obj_delete_list_basic_qs(self):
        self.assertEqual(len(Note.objects.all()), 6)
        customs = VeryCustomNoteResource().obj_delete_list()
        self.assertEqual(len(Note.objects.all()), 0)
    
    def test_obj_create(self):
        self.assertEqual(Note.objects.all().count(), 6)
        note = NoteResource()
        bundle = Bundle(data={
            'title': "A new post!",
            'slug': "a-new-post",
            'content': "Testing, 1, 2, 3!",
            'is_active': True
        })
        note.obj_create(bundle)
        self.assertEqual(Note.objects.all().count(), 7)
        latest = Note.objects.get(slug='a-new-post')
        self.assertEqual(latest.title, u"A new post!")
        self.assertEqual(latest.slug, u'a-new-post')
        self.assertEqual(latest.content, u'Testing, 1, 2, 3!')
        self.assertEqual(latest.is_active, True)
        
        self.assertEqual(Note.objects.all().count(), 7)
        note = RelatedNoteResource()
        related_bundle = Bundle(data={
            'title': "Yet another new post!",
            'slug': "yet-another-new-post",
            'content': "WHEEEEEE!",
            'is_active': True,
            'author': '/api/v1/users/1/',
            'subjects': ['/api/v1/subjects/2/'],
        })
        note.obj_create(related_bundle)
        self.assertEqual(Note.objects.all().count(), 8)
        latest = Note.objects.get(slug='yet-another-new-post')
        self.assertEqual(latest.title, u"Yet another new post!")
        self.assertEqual(latest.slug, u'yet-another-new-post')
        self.assertEqual(latest.content, u'WHEEEEEE!')
        self.assertEqual(latest.is_active, True)
        self.assertEqual(latest.author.username, u'johndoe')
        self.assertEqual(latest.subjects.all().count(), 1)
        self.assertEqual([sub.id for sub in latest.subjects.all()], [2])
    
    def test_obj_update(self):
        self.assertEqual(Note.objects.all().count(), 6)
        note = NoteResource()
        note_obj = note.obj_get(obj_id=1)
        note_bundle = note.full_dehydrate(note_obj)
        note_bundle.data['title'] = 'Whee!'
        # FIXME: Inconsistent API. ``obj_id`` in some places, ``id`` in others.
        note.obj_update(note_bundle, id=1)
        self.assertEqual(Note.objects.all().count(), 6)
        numero_uno = Note.objects.get(pk=1)
        self.assertEqual(numero_uno.title, u'Whee!')
        self.assertEqual(numero_uno.slug, u'first-post')
        self.assertEqual(numero_uno.content, u'This is my very first post using my shiny new API. Pretty sweet, huh?')
        self.assertEqual(numero_uno.is_active, True)
        
        self.assertEqual(Note.objects.all().count(), 6)
        note = RelatedNoteResource()
        related_obj = note.obj_get(obj_id=1)
        related_bundle = Bundle(obj=related_obj, data={
            'title': "Yet another new post!",
            'slug': "yet-another-new-post",
            'content': "WHEEEEEE!",
            'is_active': True,
            'author': '/api/v1/users/2/',
            'subjects': ['/api/v1/subjects/2/', '/api/v1/subjects/1/'],
        })
        # FIXME: Inconsistent API. ``obj_id`` in some places, ``id`` in others.
        note.obj_update(related_bundle, id=1)
        self.assertEqual(Note.objects.all().count(), 6)
        latest = Note.objects.get(slug='yet-another-new-post')
        self.assertEqual(latest.title, u"Yet another new post!")
        self.assertEqual(latest.slug, u'yet-another-new-post')
        self.assertEqual(latest.content, u'WHEEEEEE!')
        self.assertEqual(latest.is_active, True)
        self.assertEqual(latest.author.username, u'janedoe')
        self.assertEqual(latest.subjects.all().count(), 2)
        self.assertEqual([sub.id for sub in latest.subjects.all()], [1, 2])
    
    def test_obj_delete(self):
        self.assertEqual(Note.objects.all().count(), 6)
        note = NoteResource()
        note.obj_delete(obj_id=1)
        self.assertEqual(Note.objects.all().count(), 5)
        self.assertRaises(Note.DoesNotExist, Note.objects.get, pk=1)


class BasicAuthResourceTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_dispatch_list(self):
        resource = BasicAuthNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.dispatch_list(request)
        self.assertEqual(resp.status_code, 401)
        
        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('johndoe:pass')
        
        resp = resource.dispatch_list(request)
        self.assertEqual(resp.status_code, 200)
    
    def test_dispatch_detail(self):
        resource = BasicAuthNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.dispatch_detail(request, obj_id=1)
        self.assertEqual(resp.status_code, 401)
        
        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('johndoe:pass')
        
        resp = resource.dispatch_list(request)
        self.assertEqual(resp.status_code, 200)
