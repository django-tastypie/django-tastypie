import httplib
from testcases import TestServerTestCase
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

    def test_get_apis_json_default(self):
        connection = self.get_connection()
        connection.request('GET', '/api/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '{"businesses": {"list_endpoint": "/api/businesses/", "schema": "/api/businesses/schema/"}, "notes": {"list_endpoint": "/api/notes/", "schema": "/api/notes/schema/"}, "users": {"list_endpoint": "/api/users/", "schema": "/api/users/schema/"}}')

    def test_get_apis_json_v1(self):
        connection = self.get_connection()
        connection.request('GET', '/api/', headers={'Accept': 'application/vnd.api.v1+json'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '{"notes": {"list_endpoint": "/api/notes/", "schema": "/api/notes/schema/"}, "organizations": {"list_endpoint": "/api/organizations/", "schema": "/api/organizations/schema/"}, "users": {"list_endpoint": "/api/users/", "schema": "/api/users/schema/"}}')

    def test_get_apis_json_v2(self):
        connection = self.get_connection()
        connection.request('GET', '/api/', headers={'Accept': 'application/vnd.api.v2+json'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '{"businesses": {"list_endpoint": "/api/businesses/", "schema": "/api/businesses/schema/"}, "notes": {"list_endpoint": "/api/notes/", "schema": "/api/notes/schema/"}, "users": {"list_endpoint": "/api/users/", "schema": "/api/users/schema/"}}')

    def test_get_apis_xml_default(self):
        connection = self.get_connection()
        connection.request('GET', '/api/', headers={'Accept': 'application/xml'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><notes type="hash"><list_endpoint>/api/notes/</list_endpoint><schema>/api/notes/schema/</schema></notes><businesses type="hash"><list_endpoint>/api/businesses/</list_endpoint><schema>/api/businesses/schema/</schema></businesses><users type="hash"><list_endpoint>/api/users/</list_endpoint><schema>/api/users/schema/</schema></users></response>')

    def test_get_apis_xml_v1(self):
        connection = self.get_connection()
        connection.request('GET', '/api/', headers={'Accept': 'application/vnd.api.v1+xml'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><organizations type="hash"><list_endpoint>/api/organizations/</list_endpoint><schema>/api/organizations/schema/</schema></organizations><notes type="hash"><list_endpoint>/api/notes/</list_endpoint><schema>/api/notes/schema/</schema></notes><users type="hash"><list_endpoint>/api/users/</list_endpoint><schema>/api/users/schema/</schema></users></response>')

    def test_get_apis_xml_v2(self):
        connection = self.get_connection()
        connection.request('GET', '/api/', headers={'Accept': 'application/vnd.api.v2+xml'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><notes type="hash"><list_endpoint>/api/notes/</list_endpoint><schema>/api/notes/schema/</schema></notes><businesses type="hash"><list_endpoint>/api/businesses/</list_endpoint><schema>/api/businesses/schema/</schema></businesses><users type="hash"><list_endpoint>/api/users/</list_endpoint><schema>/api/users/schema/</schema></users></response>')

    def test_get_list(self):
        connection = self.get_connection()

        expected_v1_json = '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 2}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": "1", "is_active": true, "resource_uri": "/api/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00", "user": "/api/users/1/"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": "2", "is_active": true, "resource_uri": "/api/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00", "user": "/api/users/1/"}]}'
        expected_v2_json = '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 2}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "custom_field": "Whatever you want", "id": "1", "is_active": true, "resource_uri": "/api/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00", "user": "/api/users/1/"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "custom_field": "Whatever you want", "id": "2", "is_active": true, "resource_uri": "/api/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00", "user": "/api/users/1/"}]}'
        
        # Default
        connection.request('GET', '/api/notes/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), expected_v2_json)

        # v1
        connection.request('GET', '/api/notes/', headers={'Accept': 'application/vnd.api.v1+json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), expected_v1_json)

        # v2
        connection.request('GET', '/api/notes/', headers={'Accept': 'application/vnd.api.v2+json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), expected_v2_json)

    def test_post_object_default(self):
        connection = self.get_connection()

        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/users/1/"}'
        connection.request('POST', '/api/notes/', body=post_data, headers={'Accept': 'application/json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/notes/3/')

        # make sure posted object exists
        connection.request('GET', '/api/notes/3/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/users/1/')

    def test_post_object_v1(self):
        """
        Test a POST with api_name v1 specified.  This should be just the
        same as the default, as we're not posting to the new resource.
        """
        connection = self.get_connection()

        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/users/1/"}'
        connection.request('POST', '/api/notes/', body=post_data, headers={'Accept': 'application/vnd.api.v1+json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/notes/3/')

        # make sure posted object exists
        connection.request('GET', '/api/notes/3/', headers={'Accept': 'application/vnd.api.v1+json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/users/1/')

    def test_post_object_v2(self):
        """
        Test a POST with api_name v2 specified.  This should be just the
        same as the default, as v2 is set to default.
        """
        connection = self.get_connection()

        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/users/1/"}'
        connection.request('POST', '/api/notes/', body=post_data, headers={'Accept': 'application/vnd.api.v2+json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/notes/3/')

        # make sure posted object exists
        connection.request('GET', '/api/notes/3/', headers={'Accept': 'application/vnd.api.v2+json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/users/1/')

    def test_post_object_to_nonexistent_resource(self):
        """
        We POST (in v1) to a resource that doesn't exist in v1 -- it only exists in v2.
        We also POST (in v2) to a resource that doesn't exist in v2 -- it only exists in v1.
        These should produce a 404 error.
        """
        connection = self.get_connection()

        post_data = '{"content": "A new business.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/users/1/"}'
        connection.request('POST', '/api/businesses/', body=post_data, headers={'Accept': 'application/vnd.api.v1+json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 404)

        post_data = '{"content": "A new business.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/users/1/"}'
        connection.request('POST', '/api/organizations/', body=post_data, headers={'Accept': 'application/vnd.api.v2+json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 404)

    def test_post_content_type(self):
        """
        POSTing with a Content-type containing the API name should be fine.
        """
        connection = self.get_connection()

        post_data = '{"description": "A new business.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/users/1/"}'
        connection.request('POST', '/api/businesses/', body=post_data, headers={'Accept': 'application/vnd.api.v2+json', 'Content-type': 'application/vnd.api.v2+json'})

        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/businesses/1/')

        # make sure posted object exists
        connection.request('GET', '/api/businesses/1/', headers={'Accept': 'application/vnd.api.v2+json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)
        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['description'], 'A new business.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/users/1/')

    def test_return_content_type(self):
        """
        The API should return a Content-type including the api name.
        """
        connection = self.get_connection()

        # Default
        connection.request('GET', '/api/notes/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)

        # Checking headers is gross because we're not using the standard Django
        # client.get(). Keeping convention.
        has_content_type = False
        for header in response.msg.headers:
            if header.startswith('Content-Type: application/vnd.api.v2+json'):
                has_content_type = True
        self.assertTrue(has_content_type) 

        # v1
        connection.request('GET', '/api/notes/', headers={'Accept': 'application/vnd.api.v1+json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)

        has_content_type = False
        for header in response.msg.headers:
            if header.startswith('Content-Type: application/vnd.api.v1+json'):
                has_content_type = True
        self.assertTrue(has_content_type)

        # v2
        connection.request('GET', '/api/notes/', headers={'Accept': 'application/vnd.api.v2+json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)

        has_content_type = False
        for header in response.msg.headers:
            if header.startswith('Content-Type: application/vnd.api.v2+json'):
                has_content_type = True
        self.assertTrue(has_content_type)

    def test_get_custom_value(self):
        # A custom value that's in v2 but not in v1.
        connection = self.get_connection()

        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/users/1/"}'
        connection.request('POST', '/api/notes/', body=post_data, headers={'Accept': 'application/json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)

        # Get v1 object.
        connection.request('GET', '/api/notes/3/', headers={'Accept': 'application/vnd.api.v1+json'})
        response = connection.getresponse()
        connection.close()

        data = response.read()
        obj = json.loads(data)
        self.assertFalse(hasattr(obj, 'custom_field'))

        # Get v2 object.
        connection.request('GET', '/api/notes/3/', headers={'Accept': 'application/vnd.api.v2+json'})
        response = connection.getresponse()
        connection.close()

        data = response.read()
        obj = json.loads(data)
        self.assertEqual(obj['custom_field'], 'Whatever you want')
