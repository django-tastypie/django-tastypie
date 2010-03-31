from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import HttpRequest, QueryDict
from django.test import TestCase
from tastypie.representations.models import ModelRepresentation
from tastypie.resources import Resource
from tastypie.serializers import Serializer
from core.models import Note


class NoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.filter(is_active=True)
    
    def get_resource_uri(self):
        return '/api/v1/notes/%s/' % self.instance.id


class DetailedNoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.filter(is_active=True)
    
    def get_resource_uri(self):
        return '/api/v1/notes/%s/' % self.instance.id


class CustomSerializer(Serializer):
    pass


class NoteResource(Resource):
    representation = NoteRepresentation
    url_prefix = 'notes'


class ResourceTestCase(TestCase):
    fixtures = ['note_testdata.json']
    
    def test_init(self):
        # No representations.
        self.assertRaises(ImproperlyConfigured, Resource)
        
        # No detail representation.
        self.assertRaises(ImproperlyConfigured, Resource, list_representation=NoteResource)
        
        # No url_prefix.
        self.assertRaises(ImproperlyConfigured, Resource, representation=NoteResource)
        
        # Very minimal & stock.
        resource_1 = NoteResource()
        self.assertEqual(issubclass(resource_1.list_representation, NoteRepresentation), True)
        self.assertEqual(issubclass(resource_1.detail_representation, NoteRepresentation), True)
        self.assertEqual(resource_1.url_prefix, 'notes')
        self.assertEqual(resource_1.per_page, 20)
        self.assertEqual(resource_1.list_allowed_methods, ['get', 'post', 'put', 'delete'])
        self.assertEqual(resource_1.detail_allowed_methods, ['get', 'post', 'put', 'delete'])
        self.assertEqual(isinstance(resource_1.serializer, Serializer), True)
        
        # Lightly custom.
        resource_2 = NoteResource(
            representation=NoteRepresentation,
            url_prefix='noteish',
            allowed_methods=['get'],
        )
        self.assertEqual(issubclass(resource_2.list_representation, NoteRepresentation), True)
        self.assertEqual(issubclass(resource_2.detail_representation, NoteRepresentation), True)
        self.assertEqual(resource_2.url_prefix, 'noteish')
        self.assertEqual(resource_2.per_page, 20)
        self.assertEqual(resource_2.list_allowed_methods, ['get'])
        self.assertEqual(resource_2.detail_allowed_methods, ['get'])
        self.assertEqual(isinstance(resource_2.serializer, Serializer), True)
        
        # Highly custom.
        resource_3 = NoteResource(
            list_representation=NoteRepresentation,
            detail_representation=DetailedNoteRepresentation,
            per_page=50,
            url_prefix='notey',
            serializer=CustomSerializer(),
            list_allowed_methods=['get'],
            detail_allowed_methods=['get', 'post', 'put']
        )
        self.assertEqual(issubclass(resource_3.list_representation, NoteRepresentation), True)
        self.assertEqual(issubclass(resource_3.detail_representation, DetailedNoteRepresentation), True)
        self.assertEqual(resource_3.url_prefix, 'notey')
        self.assertEqual(resource_3.per_page, 50)
        self.assertEqual(resource_3.list_allowed_methods, ['get'])
        self.assertEqual(resource_3.detail_allowed_methods, ['get', 'post', 'put'])
        self.assertEqual(isinstance(resource_3.serializer, CustomSerializer), True)
    
    def test_urls(self):
        resource = NoteResource()
        patterns = resource.urls
        self.assertEqual(len(patterns), 2)
        self.assertEqual([pattern.name for pattern in patterns], ['api_notes_dispatch_list', 'api_notes_dispatch_detail'])
    
    def test_determine_format(self):
        resource = NoteResource()
        request = HttpRequest()
        
        # Default.
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        # Test forcing the ``format`` parameter.
        request.GET = {'format': 'json'}
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        request.GET = {'format': 'xml'}
        self.assertEqual(resource.determine_format(request), 'application/xml')
        
        request.GET = {'format': 'yaml'}
        self.assertEqual(resource.determine_format(request), 'text/yaml')
        
        request.GET = {'format': 'foo'}
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        # Test the ``Accept`` header.
        request.META = {'HTTP_ACCEPT': 'application/json'}
        self.assertEqual(resource.determine_format(request), 'application/json')
        
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
    
    def test_get_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"results": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30 20:05:00", "is_active": true, "slug": "first-post", "title": "First Post!", "updated": "2010-03-30 20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31 20:05:00", "is_active": true, "slug": "another-post", "title": "Another Post", "updated": "2010-03-31 20:05:00"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "2010-04-01 20:05:00", "is_active": true, "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "2010-04-01 20:05:00"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "2010-04-02 10:05:00", "is_active": true, "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "2010-04-02 10:05:00"}]}')
    
    def test_get_detail(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        
        resp = resource.get_detail(request, 1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30 20:05:00", "is_active": true, "slug": "first-post", "title": "First Post!", "updated": "2010-03-30 20:05:00"}')
        
        resp = resource.get_detail(request, 2)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31 20:05:00", "is_active": true, "slug": "another-post", "title": "Another Post", "updated": "2010-03-31 20:05:00"}')
        
        resp = resource.get_detail(request, 300)
        self.assertEqual(resp.status_code, 410)
    
    def test_put_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        
        resp = resource.post_detail(request, 2)
        self.assertEqual(resp.status_code, 501)
    
    def test_put_detail(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request._raw_post_data = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}'
        
        resp = resource.put_detail(request, obj_id=10)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='cat-is-back')
        self.assertEqual(new_note.content, "The cat is back. The dog coughed him up out back.")
        
        request._raw_post_data = '{"content": "The cat is gone again. I think it was the rabbits that ate him this time.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Gone", "updated": "2010-04-03 20:05:00"}'
        
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
        request._raw_post_data = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}'
        
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
        
        resp = resource.post_detail(request, 2)
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
        
        resp = resource.delete_detail(request, 2)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Note.objects.count(), 5)
    
    def test_dispatch_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.dispatch_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"results": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30 20:05:00", "is_active": true, "slug": "first-post", "title": "First Post!", "updated": "2010-03-30 20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31 20:05:00", "is_active": true, "slug": "another-post", "title": "Another Post", "updated": "2010-03-31 20:05:00"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "2010-04-01 20:05:00", "is_active": true, "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "2010-04-01 20:05:00"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "2010-04-02 10:05:00", "is_active": true, "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "2010-04-02 10:05:00"}]}')
    
    def test_dispatch_detail(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resp = resource.dispatch_detail(request, obj_id=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30 20:05:00", "is_active": true, "slug": "first-post", "title": "First Post!", "updated": "2010-03-30 20:05:00"}')
