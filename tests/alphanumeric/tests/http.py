from testcases import TestServerTestCase
import httplib
try:
    import json
except ImportError:
    import simplejson as json


class HTTPTestCase(TestServerTestCase):
    def setUp(self):
        self.start_test_server(address='localhost', port=8001)

    def tearDown(self):
        self.stop_test_server()

    def get_connection(self):
        return httplib.HTTPConnection('localhost', 8001)

    def test_get_apis_json(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '{"products": "/api/v1/products/"}')

    def test_get_apis_xml(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/', headers={'Accept': 'application/xml'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, "<?xml version='1.0' encoding='utf-8'?>\n<response><products>/api/v1/products/</products></response>")

    def test_get_list(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/products/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)
        expected = {"meta": {"limit": 20, "next": None, "offset": 0, "previous": None, "total_count": 6},
                    "objects": [{"artnr": "11111", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "name": "Skateboardrampe", "resource_uri": "/api/v1/products/11111/", "updated": "Tue, 30 Mar 2010 20:05:00 -0500"},
                                {"artnr": "76123", "created": "Tue, 4 May 2010 20:05:00 -0500", "name": "Bigwheel", "resource_uri": "/api/v1/products/76123/", "updated": "Tue, 4 May 2010 20:05:00 -0500"},
                                {"artnr": "WS65150-01", "created": "Tue, 4 May 2010 20:05:00 -0500", "name": "Trampolin", "resource_uri": "/api/v1/products/WS65150-01/", "updated": "Tue, 4 May 2010 20:05:00 -0500"},
                                {"artnr": "65100A-01", "created": "Tue, 4 May 2010 20:05:00 -0500", "name": "Laufrad", "resource_uri": "/api/v1/products/65100A-01/", "updated": "Tue, 4 May 2010 20:05:00 -0500"},
                                {"artnr": "76123/01", "created": "Tue, 4 May 2010 20:05:00 -0500", "name": "Bigwheel", "resource_uri": "/api/v1/products/76123/01/", "updated": "Tue, 4 May 2010 20:05:00 -0500"},
                                {"artnr": "WS65150/01-01", "created": "Tue, 4 May 2010 20:05:00 -0500", "name": "Trampolin", "resource_uri": "/api/v1/products/WS65150/01-01/", "updated": "Tue, 4 May 2010 20:05:00 -0500"}]
                    }
        self.assertEqual(json.loads(response.read()), expected)

    def test_post_object(self):
        connection = self.get_connection()
        post_data = '{"artnr": "A76124/03", "name": "Bigwheel XXL"}'
        connection.request('POST', '/api/v1/products/', body=post_data, headers={'Accept': 'application/json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/v1/products/A76124/03/')
    
        # make sure posted object exists
        connection.request('GET', '/api/v1/products/A76124/03/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
    
        self.assertEqual(response.status, 200)
    
        data = response.read()
        obj = json.loads(data)
    
        self.assertEqual(obj['name'], 'Bigwheel XXL')
        self.assertEqual(obj['artnr'], 'A76124/03')
