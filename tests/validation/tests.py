from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest
from django.test import TestCase
import django

if django.get_version() < '1.2':
    import monkeypatch_django_test_put

try:
    import json
except ImportError:
    import simplejson as json

from basic.models import Note

class FilteringErrorsTestCase(TestCase):
    urls = 'validation.api.urls'
    
    def test_valid_date(self):
        resp = self.client.get('/api/v1/notes/', data={'format': 'json',
                                                      'created__gte':'2010-03-31'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized['objects']),
                         Note.objects.filter(created__gte='2010-03-31').count())
        

    def test_invalid_date(self):
        resp = self.client.get('/api/v1/notes/', data={'format': 'json',
                                                      'created__gte':'foo-baz-bar'})
        self.assertEqual(resp.status_code, 400)
        
class PutValidationTestCase(TestCase):
    urls = 'validation.api.urls'
    
    def test_put_validation(self):
        resp = self.client.get('/api/v1/users/', data={'format': 'json'})
        deserialized = json.loads(resp.content)
        user = deserialized['objects'][0]
        resp = self.client.put(user['resource_uri'], data=json.dumps(user), 
                               content_type="application/json")
        self.assertEquals(resp.status_code, 204, '%s: %s' % (resp.status_code, resp.content))
        resp = self.client.get(user['resource_uri'])
        updated = json.loads(resp.content)
        self.assertEquals(user, updated)
