from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase
try:
    import json
except ImportError:
    import simplejson as json


class ViewsTestCase(TestCase):
    def test_gets(self):
        resp = self.client.get('/api/v1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['notes'], u'/api/v1/notes/')
        
        resp = self.client.get('/api/v1/notes/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'First Post!', u'Another Post'])
        
        resp = self.client.get('/api/v1/notes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 9)
        self.assertEqual(deserialized['title'], u'First Post!')
        
        resp = self.client.get('/api/v1/notes/set/2;1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Another Post', u'First Post!'])
    
    def test_posts(self):
        request = HttpRequest()
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        request._raw_post_data = post_data
        
        resp = self.client.post('/api/v1/notes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/notes/3/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/notes/3/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')


class ViewsWithoutSlashesTestCase(TestCase):
    urls = 'basic.api.slashless_urls'
    
    def setUp(self):
        super(ViewsWithoutSlashesTestCase, self).setUp()
        
        # Stow.
        self.old_append_slashes = settings.APPEND_SLASH
        self.old_missing_slashes = getattr(settings, 'TASTYPIE_ALLOW_MISSING_SLASH', False)
        self.old_debug = settings.DEBUG
        settings.APPEND_SLASH = False
        settings.TASTYPIE_ALLOW_MISSING_SLASH = True
        settings.DEBUG = True
    
    def tearDown(self):
        # Restore.
        settings.APPEND_SLASH = self.old_append_slashes
        settings.TASTYPIE_ALLOW_MISSING_SLASH = self.old_missing_slashes
        settings.DEBUG = self.old_debug
        
        super(ViewsWithoutSlashesTestCase, self).tearDown()
        
    def test_gets_without_trailing_slash(self):
        resp = self.client.get('/api/v1', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['notes'], u'/api/v1/notes')
        
        resp = self.client.get('/api/v1/notes', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'First Post!', u'Another Post'])
        
        resp = self.client.get('/api/v1/notes/1', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 9)
        self.assertEqual(deserialized['title'], u'First Post!')
        
        # Due to the way Django parses URLs, ``get_multiple`` won't work without
        # a trailing slash. This will cause the ``get_detail`` to match
        # instead, resulting in a 500.
        resp = self.client.get('/api/v1/notes/set/2;1', data={'format': 'json'})
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(json.loads(resp.content)["error_message"], "Invalid resource lookup data provided (mismatched type).")
