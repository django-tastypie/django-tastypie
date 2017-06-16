import json

from django.http import HttpRequest
from django.test.utils import override_settings

from testcases import TestCaseWithFixture


class ViewsTestCase(TestCaseWithFixture):
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

        # slashes, and more dots
        resp = self.client.get('/api/v1/products/set/76123/01;WS77.86/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['name'] for obj in deserialized['objects']], [u'Bigwheel', u'Ant Farm'])

    def test_posts(self):
        request = HttpRequest()
        post_data = '{"name": "Ball", "artnr": "12345"}'
        request._body = post_data

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp['location'].endswith('/api/v1/products/12345/'))

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/12345/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Ball')
        self.assertEqual(obj['artnr'], '12345')

        # With appended characters
        request = HttpRequest()
        post_data = '{"name": "Ball 2", "artnr": "12345ABC"}'
        request._body = post_data

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp['location'].endswith('/api/v1/products/12345ABC/'))

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/12345ABC/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Ball 2')
        self.assertEqual(obj['artnr'], '12345ABC')

        # With prepended characters
        request = HttpRequest()
        post_data = '{"name": "Ball 3", "artnr": "WK12345"}'
        request._body = post_data

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp['location'].endswith('/api/v1/products/WK12345/'))

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/WK12345/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Ball 3')
        self.assertEqual(obj['artnr'], 'WK12345')

        # Now Primary Keys with Slashes
        request = HttpRequest()
        post_data = '{"name": "Bigwheel", "artnr": "76123/03"}'
        request._body = post_data

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp['location'].endswith('/api/v1/products/76123/03/'))

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/76123/03/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Bigwheel')
        self.assertEqual(obj['artnr'], '76123/03')

        request = HttpRequest()
        post_data = '{"name": "Trampolin", "artnr": "WS65150/02"}'
        request._body = post_data

        resp = self.client.post('/api/v1/products/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp['location'].endswith('/api/v1/products/WS65150/02/'))

        # make sure posted object exists
        resp = self.client.get('/api/v1/products/WS65150/02/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['name'], 'Trampolin')
        self.assertEqual(obj['artnr'], 'WS65150/02')


@override_settings(DEBUG=True)
class MoreViewsTestCase(TestCaseWithFixture):
    def test_get_apis_json(self):
        response = self.client.get('/api/v1/', HTTP_ACCEPT='application/json')
        data = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200, data)
        self.assertEqual(data, '{"products": {"list_endpoint": "/api/v1/products/", "schema": "/api/v1/products/schema/"}}')

    def test_get_apis_xml(self):
        response = self.client.get('/api/v1/', HTTP_ACCEPT='application/xml')
        data = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200, data)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><products type="hash"><list_endpoint>/api/v1/products/</list_endpoint><schema>/api/v1/products/schema/</schema></products></response>')

    def test_get_list(self):
        response = self.client.get('/api/v1/products/', HTTP_ACCEPT='application/json')
        data = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200, data)
        expected = {
            'meta': {
                'previous': None,
                'total_count': 7,
                'offset': 0,
                'limit': 20,
                'next': None
            },
            'objects': [
                {
                    'updated': '2010-03-30T20:05:00',
                    'resource_uri': '/api/v1/products/11111/',
                    'name': 'Skateboardrampe',
                    'artnr': '11111',
                    'created': '2010-03-30T20:05:00'
                },
                {
                    'updated': '2010-05-04T20:05:00',
                    'resource_uri': '/api/v1/products/76123/',
                    'name': 'Bigwheel',
                    'artnr': '76123',
                    'created': '2010-05-04T20:05:00'
                },
                {
                    'updated': '2010-05-04T20:05:00',
                    'resource_uri': '/api/v1/products/WS65150-01/',
                    'name': 'Trampolin',
                    'artnr': 'WS65150-01',
                    'created': '2010-05-04T20:05:00'
                },
                {
                    'updated': '2010-05-04T20:05:00',
                    'resource_uri': '/api/v1/products/65100A-01/',
                    'name': 'Laufrad',
                    'artnr': '65100A-01',
                    'created': '2010-05-04T20:05:00'
                },
                {
                    'updated': '2010-05-04T20:05:00',
                    'resource_uri': '/api/v1/products/76123/01/',
                    'name': 'Bigwheel',
                    'artnr': '76123/01',
                    'created': '2010-05-04T20:05:00'
                },
                {
                    'updated': '2010-05-04T20:05:00',
                    'resource_uri': '/api/v1/products/WS65150/01-01/',
                    'name': 'Human Hamsterball',
                    'artnr': 'WS65150/01-01',
                    'created': '2010-05-04T20:05:00'
                },
                {
                    'updated': '2010-05-04T20:05:00',
                    'resource_uri': '/api/v1/products/WS77.86/',
                    'name': 'Ant Farm',
                    'artnr': 'WS77.86',
                    'created': '2010-05-04T20:05:00'
                }
            ]
        }

        resp = json.loads(data)

        # testing separately to help locate issues
        self.assertEqual(resp['meta'], expected['meta'])
        self.assertEqual(resp['objects'], expected['objects'])

    def test_post_object(self):
        post_data = '{"artnr": "A76124/03", "name": "Bigwheel XXL"}'
        response = self.client.post('/api/v1/products/', data=post_data, HTTP_ACCEPT='application/json', content_type='application/json')
        data = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 201, data)
        location = response['Location']
        self.assertTrue(location.endswith('/api/v1/products/A76124/03/'))

        # make sure posted object exists
        response = self.client.get('/api/v1/products/A76124/03/', HTTP_ACCEPT='application/json')

        data = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200, data)

        obj = json.loads(data)

        self.assertEqual(obj['name'], 'Bigwheel XXL')
        self.assertEqual(obj['artnr'], 'A76124/03')
