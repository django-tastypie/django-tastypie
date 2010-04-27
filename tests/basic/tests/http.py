from tests.testcases import TestServerTestCase
import httplib

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
        self.assertEqual(data, '{"notes": "/api/v1/notes/", "users": "/api/v1/users/"}')

    def test_get_apis_xml(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/', headers={'Accept': 'application/xml'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, "<?xml version='1.0' encoding='utf-8'?>\n<response><notes>/api/v1/notes/</notes><users>/api/v1/users/</users></response>")

    def test_get_list(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/notes/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 2}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "Tue, 30 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "Tue, 30 Mar 2010 20:05:00 -0500", "user": "/api/v1/users/1/"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "Wed, 31 Mar 2010 20:05:00 -0500", "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "Wed, 31 Mar 2010 20:05:00 -0500", "user": "/api/v1/users/1/"}]}')
