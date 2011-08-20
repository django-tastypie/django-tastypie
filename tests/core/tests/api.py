from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
from tastypie.api import Api
from tastypie.exceptions import NotRegistered, BadRequest
from tastypie.resources import Resource, ModelResource
from core.models import Note


class NoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()


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

    def test_unregister(self):
        api = Api()
        api.register(NoteResource())
        api.register(UserResource(), canonical=False)
        self.assertEqual(sorted(api._registry.keys()), ['notes', 'users'])

        self.assertEqual(len(api._canonicals), 1)
        api.unregister('users')
        self.assertEqual(len(api._registry), 1)
        self.assertEqual(sorted(api._registry.keys()), ['notes'])
        self.assertEqual(len(api._canonicals), 1)

        api.unregister('notes')
        self.assertEqual(len(api._registry), 0)
        self.assertEqual(sorted(api._registry.keys()), [])

        api.unregister('users')
        self.assertEqual(len(api._registry), 0)
        self.assertEqual(sorted(api._registry.keys()), [])

    def test_canonical_resource_for(self):
        api = Api()
        note_resource = NoteResource()
        user_resource = UserResource()
        api.register(note_resource)
        api.register(user_resource)
        self.assertEqual(len(api._canonicals), 2)

        self.assertEqual(isinstance(api.canonical_resource_for('notes'), NoteResource), True)

        api_2 = Api()
        api.unregister(user_resource._meta.resource_name)
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
        self.assertEqual(resp.content, '{"notes": {"list_endpoint": "/api/v1/notes/", "schema": "/api/v1/notes/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}}')

    def test_top_level_jsonp(self):
        api = Api()
        api.register(NoteResource())
        api.register(UserResource())
        request = HttpRequest()
        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        request.GET = {'callback': 'foo'}

        resp = api.top_level(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['content-type'].split(';')[0], 'text/javascript')
        self.assertEqual(resp.content, 'foo({"notes": {"list_endpoint": "/api/v1/notes/", "schema": "/api/v1/notes/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}})')

        request = HttpRequest()
        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        request.GET = {'callback': ''}

        try:
            resp = api.top_level(request)
            self.fail("Broken callback didn't fail!")
        except BadRequest:
            # Regression: We expect this, which is fine, but this used to
            #             be an import error.
            pass
