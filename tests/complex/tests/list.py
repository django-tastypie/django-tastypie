from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase, Client
from django.utils import simplejson as json
from pprint import pprint 

class ListTestCase(TestCase):
    fixtures = ['broken_post.json']
    def test_wrong_data_sensitiveness(self):
        resp = self.client.get('/api/v1/posts/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
