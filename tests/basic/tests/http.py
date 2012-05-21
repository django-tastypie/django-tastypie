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
