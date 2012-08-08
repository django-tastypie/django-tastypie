import httplib
from testcases import TestServerTestCase
from django.utils import simplejson as json


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
        self.assertEqual(data, '{"cached_users": {"list_endpoint": "/api/v1/cached_users/", "schema": "/api/v1/cached_users/schema/"}, "notes": {"list_endpoint": "/api/v1/notes/", "schema": "/api/v1/notes/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}}')

    def test_get_apis_xml(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/', headers={'Accept': 'application/xml'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><notes type="hash"><list_endpoint>/api/v1/notes/</list_endpoint><schema>/api/v1/notes/schema/</schema></notes><cached_users type="hash"><list_endpoint>/api/v1/cached_users/</list_endpoint><schema>/api/v1/cached_users/schema/</schema></cached_users><users type="hash"><list_endpoint>/api/v1/users/</list_endpoint><schema>/api/v1/users/schema/</schema></users></response>')

    def test_get_list(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/notes/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 2}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00", "user": "/api/v1/users/1/"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00", "user": "/api/v1/users/1/"}]}')

    def test_post_object(self):
        connection = self.get_connection()
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        connection.request('POST', '/api/v1/notes/', body=post_data, headers={'Accept': 'application/json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/v1/notes/3/')

        # make sure posted object exists
        connection.request('GET', '/api/v1/notes/3/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_file_support(self):
        # We POST a multipart/form-data
        connection = self.get_connection()
        post_data = '--e35efd99c055411cb7d3c89d2a7c9dda\r\nContent-Disposition: form-data; name="slug"\r\nContent-Type: text/plain\r\n\r\ngolden gate park\r\n--e35efd99c055411cb7d3c89d2a7c9dda\r\nContent-Disposition: form-data; name="title"\r\nContent-Type: text/plain\r\n\r\nGolden Gate Park\r\n--e35efd99c055411cb7d3c89d2a7c9dda\r\nContent-Disposition: form-data; name="file"; filename="/home/philip/out.txt"\r\nContent-Type: text/plain\r\n\r\nhellothere\n\r\n--e35efd99c055411cb7d3c89d2a7c9dda\r\nContent-Disposition: form-data; name="name"\r\nContent-Type: text/plain\r\n\r\ntext_hello.txt\r\n--e35efd99c055411cb7d3c89d2a7c9dda--\r\n'
        connection.request('POST', '/api/v2/filenotes/', body=post_data, headers={'Accept': 'application/json', 'Content-Type': 'multipart/form-data; boundary=e35efd99c055411cb7d3c89d2a7c9dda'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/v2/filenotes/1/')

        # make sure posted file exists
        connection.request('GET', '/api/v2/filenotes/1/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['slug'], 'golden gate park')
        self.assertEqual(obj['title'], 'Golden Gate Park')
        # Can get replaced with out_<num>.txt if tests are run many times
        self.assertTrue(obj['file'].startswith('files/out') and obj['file'].endswith('.txt'))

        # Now we PUT a multipart/form-data
        connection = self.get_connection()
        post_data = '--e35efd99c055411cb7d3c89d2a7c9dda\r\nContent-Disposition: form-data; name="slug"\r\nContent-Type: text/plain\r\n\r\ngolden gate park\r\n--e35efd99c055411cb7d3c89d2a7c9dda\r\nContent-Disposition: form-data; name="title"\r\nContent-Type: text/plain\r\n\r\nGolden GATE Park\r\n--e35efd99c055411cb7d3c89d2a7c9dda\r\nContent-Disposition: form-data; name="file"; filename="/home/philip/out.txt"\r\nContent-Type: text/plain\r\n\r\nhellothere\n\r\n--e35efd99c055411cb7d3c89d2a7c9dda\r\nContent-Disposition: form-data; name="name"\r\nContent-Type: text/plain\r\n\r\ntext_hello.txt\r\n--e35efd99c055411cb7d3c89d2a7c9dda--\r\n'
        connection.request('PUT', '/api/v2/filenotes/1/', body=post_data, headers={'Accept': 'application/json', 'Content-Type': 'multipart/form-data; boundary=e35efd99c055411cb7d3c89d2a7c9dda'})
        response = connection.getresponse()
        self.assertEqual(response.status, 204)

        # make sure put'ed file exists
        connection.request('GET', '/api/v2/filenotes/1/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['slug'], 'golden gate park')
        self.assertEqual(obj['title'], 'Golden GATE Park')
        # Can get replaced with out_<num>.txt if tests are run many times
        self.assertTrue(obj['file'].startswith('files/out') and obj['file'].endswith('.txt'))

    def test_cache_control(self):
        """Ensure that resources can specify custom cache control directives"""
        connection = self.get_connection()
        connection.request('GET', '/api/v1/cached_users/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)

        headers = dict(response.getheaders())
        self.assertEqual(headers['cache-control'], "max-age=3600",
                         "Resource-defined Cache-Control headers should be unmodified")
        self.assertTrue('"johndoe"' in response.read())
