from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest
from django.test import TestCase

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
        
