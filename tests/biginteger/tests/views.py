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
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(deserialized['products'], {'list_endpoint': '/api/v1/products/', 'schema': '/api/v1/products/schema/'})

        resp = self.client.get('/api/v1/products/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 6)
        self.assertEqual([obj['name'] for obj in deserialized['objects']],
                         [u'Skateboardrampe', u'Bigwheel', u'Trampolin', u'Laufrad', u'Bigwheel', u'Trampolin'])

        resp = self.client.get('/api/v1/products/9007199254740990/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], u'Skateboardrampe')

        resp = self.client.get('/api/v1/products/set/9007199254740990;9007199254740991/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Skateboardrampe', u'Bigwheel'])

        # Same tests with \w+ instead of \d+ for primary key regexp:
        resp = self.client.get('/api/v1/products/9007199254740992/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], u'Trampolin')

        resp = self.client.get('/api/v1/products/set/9007199254740992;9007199254740980/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Trampolin', u'Laufrad'])

        resp = self.client.get('/api/v1/products/set/9007199254740981;9007199254740980/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Bigwheel', u'Laufrad'])

        resp = self.client.get('/api/v1/products/9007199254740992/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], u'Trampolin')

        resp = self.client.get('/api/v1/products/set/9007199254740991;9007199254740982/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Bigwheel', u'Trampolin'])

    def test_posts(self):
        request = HttpRequest()
        post_data = '{"name": "Ball", "artnr": 12345}'
        request._raw_post_data = post_data

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/products/12345/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/12345/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['name'], 'Ball')
        self.assertEqual(obj['artnr'], 12345)

        # With appended characters
        request = HttpRequest()
        post_data = '{"name": "Ball 2", "artnr": 56789}'
        request._raw_post_data = post_data

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/products/56789/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/56789/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['name'], 'Ball 2')
        self.assertEqual(obj['artnr'], 56789)
