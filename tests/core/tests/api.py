import json

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings

from tastypie.api import Api
from tastypie.exceptions import NotRegistered, BadRequest
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer

from core.models import Note
from core.utils import adjust_schema
User = get_user_model()


class NoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()


@override_settings(ROOT_URLCONF='core.tests.api_urls')
class ApiTestCase(TestCase):
    def test_register(self):
        # NOTE: these have all been registered in core.tests.api_urls
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

        self.assertRaises(ValueError, api.register, NoteResource)

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
        self.assertEqual(resp.content.decode('utf-8'), '{"notes": {"list_endpoint": "/api/v1/notes/", "schema": "/api/v1/notes/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}}')

    def test_top_level_include_schema_content(self):
        api = Api()

        note_resource = NoteResource()
        user_resource = UserResource()

        api.register(note_resource)
        api.register(user_resource)

        request = HttpRequest()
        request.GET = {'fullschema': 'true'}

        resp = api.top_level(request)
        self.assertEqual(resp.status_code, 200)

        content = json.loads(resp.content.decode('utf-8'))

        content['notes']['schema'] = adjust_schema(content['notes']['schema'])
        content['users']['schema'] = adjust_schema(content['users']['schema'])

        dummy_request = HttpRequest()
        dummy_request.method = 'GET'

        notes_schema = adjust_schema(json.loads(note_resource.get_schema(dummy_request).content.decode('utf-8')))
        user_schema = adjust_schema(json.loads(user_resource.get_schema(dummy_request).content.decode('utf-8')))

        self.assertEqual(content['notes']['list_endpoint'], '/api/v1/notes/')
        self.assertEqual(content['notes']['schema'], notes_schema)

        self.assertEqual(content['users']['list_endpoint'], '/api/v1/users/')
        self.assertEqual(content['users']['schema'], user_schema)

    def test_top_level_jsonp(self):
        api = Api()
        api.serializer.formats = ['jsonp']
        api.register(NoteResource())
        api.register(UserResource())
        request = HttpRequest()
        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        request.GET = {'callback': 'foo'}

        resp = api.top_level(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['content-type'].split(';')[0], 'text/javascript')
        self.assertEqual(resp.content.decode('utf-8'), 'foo({"notes": {"list_endpoint": "/api/v1/notes/", "schema": "/api/v1/notes/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}})')

        request = HttpRequest()
        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        request.GET = {'callback': ''}

        # Regression: We expect this, which is fine, but this used to
        #             be an import error.
        with self.assertRaises(BadRequest):
            api.top_level(request)

    def test_jsonp_not_on_by_default(self):
        api = Api()
        api.register(NoteResource())
        api.register(UserResource())
        request = HttpRequest()
        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        request.GET = {'callback': 'foo'}

        resp = api.top_level(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['content-type'].split(';')[0], 'application/json')
        self.assertFalse("foo" in resp.content.decode('utf-8'))

    def test_custom_api_serializer(self):
        """Confirm that an Api can use a custom serializer"""

        # Origin: https://github.com/django-tastypie/django-tastypie/pull/817

        class JSONSerializer(Serializer):
            formats = ('json', )

        api = Api(serializer_class=JSONSerializer)
        api.register(NoteResource())

        request = HttpRequest()
        request.META = {'HTTP_ACCEPT': 'text/javascript'}

        resp = api.top_level(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['content-type'], 'application/json',
                         msg="Expected application/json response but received %s" % resp['content-type'])

        request = HttpRequest()
        request.META = {'HTTP_ACCEPT': 'application/xml'}

        resp = api.top_level(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['content-type'], 'application/json',
                         msg="Expected application/json response but received %s" % resp['content-type'])
