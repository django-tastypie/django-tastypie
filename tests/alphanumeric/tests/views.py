import django
from django.http import HttpRequest
from django.test import TestCase
import json


class ViewsTestCase(TestCase):
    def setUp(self):
        if django.VERSION >= (1, 4):
            self.body_attr = "body"
        else:
            self.body_attr = "raw_post_data"
        super(ViewsTestCase, self).setUp()

    def test_gets(self):
        resp = self.client.get('/api/v1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(deserialized['products'], {'list_endpoint': '/api/v1/products/', 'schema': '/api/v1/products/schema/'})

        resp = self.client.get('/api/v1/products/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 7)
        self.assertEqual([obj['name'] for obj in deserialized['objects']],
                         [u'Skateboardrampe', u'Bigwheel', u'Trampolin', u'Laufrad', u'Bigwheel', u'Human Hamsterball', u'Ant Farm'])

        resp = self.client.get('/api/v1/products/11111/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], u'Skateboardrampe')

        resp = self.client.get('/api/v1/products/set/11111;76123/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Skateboardrampe', u'Bigwheel'])

        # Same tests with \w+ instead of \d+ for primary key regexp:
        resp = self.client.get('/api/v1/products/WS65150-01/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], u'Trampolin')

        resp = self.client.get('/api/v1/products/set/WS65150-01;65100A-01/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Trampolin', u'Laufrad'])

        # And now Slashes
        resp = self.client.get('/api/v1/products/76123/01/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], u'Bigwheel')

        resp = self.client.get('/api/v1/products/set/76123/01;65100A-01/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Bigwheel', u'Laufrad'])

        resp = self.client.get('/api/v1/products/WS65150/01-01/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], u'Human Hamsterball')

        resp = self.client.get('/api/v1/products/set/76123/01;WS65150/01-01/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Bigwheel', u'Human Hamsterball'])

        # And now dots
        resp = self.client.get('/api/v1/products/WS77.86/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], u'Ant Farm')
        
        #slashes, and more dots
        resp = self.client.get('/api/v1/products/set/76123/01;WS77.86/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Bigwheel', u'Ant Farm'])



    def test_posts(self):
        request = HttpRequest()
        post_data = '{"name": "Ball", "artnr": "12345"}'
        setattr(request, "_" + self.body_attr, post_data)

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/products/12345/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/12345/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Ball')
        self.assertEqual(obj['artnr'], '12345')

        # With appended characters
        request = HttpRequest()
        post_data = '{"name": "Ball 2", "artnr": "12345ABC"}'
        setattr(request, "_" + self.body_attr, post_data)

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/products/12345ABC/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/12345ABC/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Ball 2')
        self.assertEqual(obj['artnr'], '12345ABC')

        # With prepended characters
        request = HttpRequest()
        post_data = '{"name": "Ball 3", "artnr": "WK12345"}'
        setattr(request, "_" + self.body_attr, post_data)

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/products/WK12345/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/WK12345/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Ball 3')
        self.assertEqual(obj['artnr'], 'WK12345')

        # Now Primary Keys with Slashes
        request = HttpRequest()
        post_data = '{"name": "Bigwheel", "artnr": "76123/03"}'
        setattr(request, "_" + self.body_attr, post_data)

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/products/76123/03/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/76123/03/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Bigwheel')
        self.assertEqual(obj['artnr'], '76123/03')

        request = HttpRequest()
        post_data = '{"name": "Trampolin", "artnr": "WS65150/02"}'
        setattr(request, "_" + self.body_attr, post_data)

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/products/WS65150/02/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/WS65150/02/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Trampolin')
        self.assertEqual(obj['artnr'], 'WS65150/02')
