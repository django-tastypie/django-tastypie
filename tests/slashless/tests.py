from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest
from django.test import TestCase
from django.utils import simplejson as json


class ViewsWithoutSlashesTestCase(TestCase):
    urls = 'slashless.api.urls'
    
    def setUp(self):
        super(ViewsWithoutSlashesTestCase, self).setUp()
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
    
    def tearDown(self):
        settings.DEBUG = self.old_debug
        super(ViewsWithoutSlashesTestCase, self).tearDown()
    
    def test_gets_without_trailing_slash(self):
        resp = self.client.get('/api/v1', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['notes'], {'list_endpoint': '/api/v1/notes', 'schema': '/api/v1/notes/schema'})
        
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
        
        resp = self.client.get('/api/v1/notes/set/2;1', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        obj_ids = [o["id"] for o in deserialized["objects"]]
        self.assertEqual(sorted(obj_ids), [1,2])
        