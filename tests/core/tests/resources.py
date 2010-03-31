from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, QueryDict
from django.test import TestCase
from tastypie.representations.models import ModelRepresentation
from tastypie.resources import Resource
from tastypie.serializers import Serializer
from core.models import Note


class NoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.filter(is_active=True)


class DetailedNoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.filter(is_active=True)


class CustomSerializer(Serializer):
    pass


class NoteResource(Resource):
    representation = NoteRepresentation
    url_prefix = 'notes'


class ResourceTestCase(TestCase):
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
        self.assertEqual(resource.determine_format(request), 'text/html')
        
        # Test forcing the ``format`` parameter.
        request.GET = {'format': 'json'}
        self.assertEqual(resource.determine_format(request), 'application/json')
        
        request.GET = {'format': 'xml'}
        self.assertEqual(resource.determine_format(request), 'application/xml')
        
        request.GET = {'format': 'yaml'}
        self.assertEqual(resource.determine_format(request), 'text/yaml')
        
        request.GET = {'format': 'foo'}
        self.assertEqual(resource.determine_format(request), 'text/html')
        
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
        pass
    
    def test_get_detail(self):
        pass
    
    def test_put_list(self):
        pass
    
    def test_put_detail(self):
        pass
    
    def test_post_list(self):
        pass
    
    def test_post_detail(self):
        pass
    
    def test_delete_list(self):
        pass
    
    def test_delete_detail(self):
        pass
    
    def test_dispatch_list(self):
        pass
    
    def test_dispatch_detail(self):
        pass
    
    
