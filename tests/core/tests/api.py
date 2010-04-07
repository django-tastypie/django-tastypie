from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
from tastypie.api import Api
from tastypie.resources import Resource
from tastypie.representations.models import ModelRepresentation
from core.models import Note


class NoteRepresentation(ModelRepresentation):
    class Meta:
        queryset = Note.objects.filter(is_active=True)
    
    def get_resource_uri(self):
        return '/api/v1/notes/%s/' % self.instance.id


class UserRepresentation(ModelRepresentation):
    class Meta:
        queryset = User.objects.all()
    
    def get_resource_uri(self):
        return '/api/v1/users/%s/' % self.instance.id


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
    
    def test_unregister(self):
        api = Api()
        api.register(NoteResource())
        api.register(UserResource())
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])
        
        api.unregister('users')
        self.assertEqual(len(api._registry), 1)
        self.assertEqual(sorted(api._registry.keys()), ['notes'])
        
        api.unregister('notes')
        self.assertEqual(len(api._registry), 0)
        self.assertEqual(sorted(api._registry.keys()), [])
        
        api.unregister('users')
        self.assertEqual(len(api._registry), 0)
        self.assertEqual(sorted(api._registry.keys()), [])
    
    def test_urls(self):
        api = Api()
        api.register(NoteResource())
        api.register(UserResource())
        
        patterns = api.urls
        self.assertEqual(len(patterns), 3)
        self.assertEqual(sorted([pattern.name for pattern in patterns if hasattr(pattern, 'name')]), ['api_v1_top_level'])
        self.assertEqual([[pattern.name for pattern in include.url_patterns if hasattr(pattern, 'name')] for include in patterns if hasattr(include, 'reverse_dict')], [['api_dispatch_list', 'api_dispatch_detail'], ['api_dispatch_list', 'api_dispatch_detail']])
        
        api = Api(api_name='v2')
        api.register(NoteResource())
        api.register(UserResource())
        
        patterns = api.urls
        self.assertEqual(len(patterns), 3)
        self.assertEqual(sorted([pattern.name for pattern in patterns if hasattr(pattern, 'name')]), ['api_v2_top_level'])
        self.assertEqual([[pattern.name for pattern in include.url_patterns if hasattr(pattern, 'name')] for include in patterns if hasattr(include, 'reverse_dict')], [['api_dispatch_list', 'api_dispatch_detail'], ['api_dispatch_list', 'api_dispatch_detail']])
    
    def test_top_level(self):
        api = Api()
        api.register(NoteResource())
        api.register(UserResource())
        request = HttpRequest()
        
        resp = api.top_level(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, '{"notes": "/api/v1/notes/", "users": "/api/v1/users/"}')
