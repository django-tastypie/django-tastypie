import json
from django.utils import six
from testcases import TestServerTestCase

try:
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection


def header_name(name):
    if six.PY3:
        return name
    else:
        return name.lower()


class HTTPTestCase(TestServerTestCase):
    def setUp(self):
        self.start_test_server(address='localhost', port=8001)

    def tearDown(self):
        self.stop_test_server()

    def get_connection(self):
        return HTTPConnection('localhost', 8001)

    def test_get_apis_json(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        data = response.read().decode('utf-8')
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '{"products": {"list_endpoint": "/api/v1/products/", "schema": "/api/v1/products/schema/"}}')

    def test_get_apis_xml(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/', headers={'Accept': 'application/xml'})
        response = connection.getresponse()
        connection.close()
        data = response.read().decode('utf-8')
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><products type="hash"><list_endpoint>/api/v1/products/</list_endpoint><schema>/api/v1/products/schema/</schema></products></response>')

    def test_get_list(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/products/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)
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
        self.maxDiff = None
        resp = json.loads(response.read().decode('utf-8'))

        #testing separately to help locate issues        
        self.assertEqual(resp['meta'], expected['meta'])
        self.assertEqual(resp['objects'], expected['objects'])

    def test_post_object(self):
        connection = self.get_connection()
        post_data = '{"artnr": "A76124/03", "name": "Bigwheel XXL"}'
        connection.request('POST', '/api/v1/products/', body=post_data, headers={'Accept': 'application/json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())[header_name('Location')], 'http://localhost:8001/api/v1/products/A76124/03/')

        # make sure posted object exists
        connection.request('GET', '/api/v1/products/A76124/03/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read().decode('utf-8')
        obj = json.loads(data)

        self.assertEqual(obj['name'], 'Bigwheel XXL')
        self.assertEqual(obj['artnr'], 'A76124/03')
