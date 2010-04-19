from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
import tastypie
from tastypie.api import Api
from tastypie.exceptions import NotRegistered, URLReverseError
from tastypie.resources import Resource
from tastypie.representations.models import ModelRepresentation
from core.models import Note


class NoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.filter(is_active=True)


class UserRepresentation(ModelRepresentation):
    class Meta:
        queryset = User.objects.all()


class NoteResource(Resource):
    representation = NoteRepresentation
    resource_name = 'notes'


class UserResource(Resource):
    representation = UserRepresentation
    resource_name = 'users'


class ApiTestCase(TestCase):
    urls = 'core.tests.api_urls'
    
    def test_register(self):
        api = Api()
        self.assertEqual(len(api._registry), 0)
        
        api.register(NoteResource())
        self.assertEqual(len(api._registry), 1)
        self.assertEqual(sorted(api._registry.keys()), ['notes'])
        
        api.register(UserResource())
        self.assertEqual(len(api._registry), 2)
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])
        
        api.register(UserResource())
        self.assertEqual(len(api._registry), 2)
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])
        
        self.assertEqual(len(api._canonicals), 2)
        api.register(UserResource(), canonical=False)
        self.assertEqual(len(api._registry), 2)
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])
        self.assertEqual(len(api._canonicals), 2)
    
    def test_global_registry(self):
        tastypie.available_apis = {}
        api = Api()
        self.assertEqual(len(api._registry), 0)
        self.assertEqual(len(tastypie.available_apis), 0)
        
        api.register(NoteResource())
        self.assertEqual(len(api._registry), 1)
        self.assertEqual(sorted(api._registry.keys()), ['notes'])
        self.assertEqual(len(tastypie.available_apis), 1)
        self.assertEqual(tastypie.available_apis['v1']['class'], api)
        self.assertEqual(tastypie.available_apis['v1']['resources'], ['notes'])
        self.assertEqual(tastypie.available_apis['v1']['representations'], {'NoteRepresentation': 'notes'})
        
        api.register(UserResource())
        self.assertEqual(len(api._registry), 2)
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])
        self.assertEqual(len(tastypie.available_apis), 1)
        self.assertEqual(tastypie.available_apis['v1']['class'], api)
        self.assertEqual(tastypie.available_apis['v1']['resources'], ['notes', 'users'])
        self.assertEqual(tastypie.available_apis['v1']['representations'], {'UserRepresentation': 'users', 'NoteRepresentation': 'notes'})
        
        api.register(UserResource())
        self.assertEqual(len(api._registry), 2)
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])
        self.assertEqual(len(tastypie.available_apis), 1)
        self.assertEqual(tastypie.available_apis['v1']['class'], api)
        self.assertEqual(tastypie.available_apis['v1']['resources'], ['notes', 'users'])
        self.assertEqual(tastypie.available_apis['v1']['representations'], {'UserRepresentation': 'users', 'NoteRepresentation': 'notes'})
        
        self.assertEqual(len(api._canonicals), 2)
        api.register(UserResource(), canonical=False)
        self.assertEqual(len(api._registry), 2)
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])
        self.assertEqual(len(api._canonicals), 2)
        self.assertEqual(len(tastypie.available_apis), 1)
        self.assertEqual(tastypie.available_apis['v1']['class'], api)
        self.assertEqual(tastypie.available_apis['v1']['resources'], ['notes', 'users'])
        self.assertEqual(tastypie.available_apis['v1']['representations'], {'UserRepresentation': 'users', 'NoteRepresentation': 'notes'})
    
    def test_unregister(self):
        tastypie.available_apis = {}
        api = Api()
        api.register(NoteResource())
        api.register(UserResource(), canonical=False)
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])
        self.assertEqual(len(tastypie.available_apis), 1)
        self.assertEqual(tastypie.available_apis['v1']['class'], api)
        self.assertEqual(tastypie.available_apis['v1']['resources'], ['notes', 'users'])
        self.assertEqual(tastypie.available_apis['v1']['representations'], {'NoteRepresentation': 'notes'})
        
        self.assertEqual(len(api._canonicals), 1)
        api.unregister('users')
        self.assertEqual(len(api._registry), 1)
        self.assertEqual(sorted(api._registry.keys()), ['notes'])
        self.assertEqual(len(api._canonicals), 1)
        self.assertEqual(tastypie.available_apis['v1']['class'], api)
        self.assertEqual(tastypie.available_apis['v1']['resources'], ['notes'])
        self.assertEqual(tastypie.available_apis['v1']['representations'], {'NoteRepresentation': 'notes'})
        
        api.unregister('notes')
        self.assertEqual(len(api._registry), 0)
        self.assertEqual(sorted(api._registry.keys()), [])
        self.assertEqual(tastypie.available_apis['v1']['class'], api)
        self.assertEqual(tastypie.available_apis['v1']['resources'], [])
        self.assertEqual(tastypie.available_apis['v1']['representations'], {})
        
        api.unregister('users')
        self.assertEqual(len(api._registry), 0)
        self.assertEqual(sorted(api._registry.keys()), [])
        self.assertEqual(tastypie.available_apis['v1']['class'], api)
        self.assertEqual(tastypie.available_apis['v1']['resources'], [])
        self.assertEqual(tastypie.available_apis['v1']['representations'], {})
    
    def test_canonical_resource_for(self):
        tastypie.available_apis = {}
        api = Api()
        note_resource = NoteResource()
        user_resource = UserResource()
        api.register(note_resource)
        api.register(user_resource)
        self.assertEqual(len(api._canonicals), 2)
        
        self.assertEqual(isinstance(api.canonical_resource_for('notes'), NoteResource), True)
        
        api_2 = Api()
        self.assertRaises(URLReverseError, tastypie._get_canonical_resource_name, api_2, NoteRepresentation)
        self.assertEqual(tastypie._get_canonical_resource_name(api.api_name, NoteRepresentation), 'notes')
        self.assertEqual(tastypie._get_canonical_resource_name(api.api_name, NoteRepresentation()), 'notes')
        self.assertEqual(tastypie._get_canonical_resource_name(api.api_name, note_resource.detail_representation), 'notes')
        self.assertEqual(tastypie._get_canonical_resource_name(api.api_name, UserRepresentation), 'users')
        self.assertEqual(tastypie._get_canonical_resource_name(api.api_name, UserRepresentation()), 'users')
        self.assertEqual(tastypie._get_canonical_resource_name(api.api_name, user_resource.detail_representation), 'users')
        
        api.unregister(user_resource.resource_name)
        self.assertRaises(NotRegistered, api.canonical_resource_for, 'users')
    
    def test_urls(self):
        api = Api()
        api.register(NoteResource())
        api.register(UserResource())
        
        patterns = api.urls
        self.assertEqual(len(patterns), 3)
        self.assertEqual(sorted([pattern.name for pattern in patterns if hasattr(pattern, 'name')]), ['api_v1_top_level'])
        self.assertEqual([[pattern.name for pattern in include.url_patterns if hasattr(pattern, 'name')] for include in patterns if hasattr(include, 'reverse_dict')], [['api_dispatch_list', 'api_get_schema', 'api_get_multiple', 'api_dispatch_detail'], ['api_dispatch_list', 'api_get_schema', 'api_get_multiple', 'api_dispatch_detail']])
        
        api = Api(api_name='v2')
        api.register(NoteResource())
        api.register(UserResource())
        
        patterns = api.urls
        self.assertEqual(len(patterns), 3)
        self.assertEqual(sorted([pattern.name for pattern in patterns if hasattr(pattern, 'name')]), ['api_v2_top_level'])
        self.assertEqual([[pattern.name for pattern in include.url_patterns if hasattr(pattern, 'name')] for include in patterns if hasattr(include, 'reverse_dict')], [['api_dispatch_list', 'api_get_schema', 'api_get_multiple', 'api_dispatch_detail'], ['api_dispatch_list', 'api_get_schema', 'api_get_multiple', 'api_dispatch_detail']])
    
    def test_top_level(self):
        api = Api()
        api.register(NoteResource())
        api.register(UserResource())
        request = HttpRequest()
        
        resp = api.top_level(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"notes": "/api/v1/notes/", "users": "/api/v1/users/"}')
