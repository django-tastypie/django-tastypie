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

    def test_get_apis_json(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '{"geonotes": {"list_endpoint": "/api/v1/geonotes/", "schema": "/api/v1/geonotes/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}}')

    def test_get_apis_xml(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/', headers={'Accept': 'application/xml'})
        response = connection.getresponse()
        connection.close()
        data = response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><users type="hash"><list_endpoint>/api/v1/users/</list_endpoint><schema>/api/v1/users/schema/</schema></users><geonotes type="hash"><list_endpoint>/api/v1/geonotes/</list_endpoint><schema>/api/v1/geonotes/schema/</schema></geonotes></response>')

    def test_get_list(self):
        connection = self.get_connection()
        connection.request('GET', '/api/v1/geonotes/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 3}, "objects": [{"content": "Wooo two points inside Golden Gate park", "created": "2010-03-30T20:05:00", "id": "1", "is_active": true, "lines": null, "points": {"coordinates": [[-122.475233, 37.768616999999999], [-122.470416, 37.767381999999998]], "type": "MultiPoint"}, "polys": null, "resource_uri": "/api/v1/geonotes/1/", "slug": "points-inside-golden-gate-park-note", "title": "Points inside Golden Gate Park note", "updated": "2012-03-07T21:47:37", "user": "/api/v1/users/1/"}, {"content": "This is a note about Golden Gate Park. It contains Golden Gate Park\'s polygon", "created": "2010-03-31T20:05:00", "id": "2", "is_active": true, "lines": null, "points": null, "polys": {"coordinates": [[[[-122.511067, 37.771276], [-122.510037, 37.766390999999999], [-122.510037, 37.763812999999999], [-122.456822, 37.765847999999998], [-122.45296, 37.766458999999998], [-122.454848, 37.773989999999998], [-122.475362, 37.773040000000002], [-122.511067, 37.771276]]]], "type": "MultiPolygon"}, "resource_uri": "/api/v1/geonotes/2/", "slug": "another-post", "title": "Golden Gate Park", "updated": "2012-03-07T21:48:48", "user": "/api/v1/users/1/"}, {"content": "A path inside Golden Gate Park! Huzzah!", "created": "2012-03-07T21:51:52", "id": "3", "is_active": true, "lines": {"coordinates": [[[-122.504544, 37.767001999999998], [-122.499995, 37.768222999999999], [-122.49596099999999, 37.769173000000002], [-122.495017, 37.769241000000001], [-122.491669, 37.770937000000004], [-122.48497500000001, 37.770733]]], "type": "MultiLineString"}, "points": null, "polys": null, "resource_uri": "/api/v1/geonotes/3/", "slug": "line-inside-golden-gate-park", "title": "Line inside Golden Gate Park", "updated": "2012-03-07T21:52:21", "user": "/api/v1/users/1/"}]}')

    def test_post_object(self):
        connection = self.get_connection()
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        connection.request('POST', '/api/v1/geonotes/', body=post_data, headers={'Accept': 'application/json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/v1/geonotes/4/')

        # make sure posted object exists
        connection.request('GET', '/api/v1/geonotes/4/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_post_geojson(self):
        connection = self.get_connection()
        post_data = """{
            "content": "A new post.", "is_active": true, "title": "New Title2",
            "slug": "new-title2", "user": "/api/v1/users/1/",
            "polys": { "type": "MultiPolygon", "coordinates": [ [ [ [ -122.511067, 37.771276 ], [ -122.510037, 37.766391 ], [ -122.510037, 37.763813 ], [ -122.456822, 37.765848 ], [ -122.452960, 37.766459 ], [ -122.454848, 37.773990 ], [ -122.475362, 37.773040 ], [ -122.511067, 37.771276 ] ] ] ] }
        }"""
        connection.request('POST', '/api/v1/geonotes/', body=post_data, headers={'Accept': 'application/json', 'Content-type': 'application/json'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/v1/geonotes/4/')

        # make sure posted object exists
        connection.request('GET', '/api/v1/geonotes/4/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')
        self.assertEqual(obj['polys'], {u'type': u'MultiPolygon', u'coordinates': [[[[-122.511067, 37.771276], [-122.510037, 37.766390999999999], [-122.510037, 37.763812999999999], [-122.456822, 37.765847999999998], [-122.45296, 37.766458999999998], [-122.454848, 37.773989999999998], [-122.475362, 37.773040000000002], [-122.511067, 37.771276]]]]})

    def test_post_xml(self):
        connection = self.get_connection()
        post_data = """<object><created>2010-03-30T20:05:00</created><polys type="null"/><is_active type="boolean">True</is_active><title>Points inside Golden Gate Park note 2</title><lines type="null"/><slug>points-inside-golden-gate-park-note-2</slug><content>A new post.</content><points type="hash"><type>MultiPoint</type><coordinates type="list"><objects><value type="float">-122.475233</value><value type="float">37.768617</value></objects><objects><value type="float">-122.470416</value><value type="float">37.767382</value></objects></coordinates></points><user>/api/v1/users/1/</user></object>"""
        connection.request('POST', '/api/v1/geonotes/', body=post_data, headers={'Accept': 'application/xml', 'Content-type': 'application/xml'})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        self.assertEqual(dict(response.getheaders())['location'], 'http://localhost:8001/api/v1/geonotes/4/')

        # make sure posted object exists
        connection.request('GET', '/api/v1/geonotes/4/', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)

        data = response.read()
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')
        # Weeeee!  GeoJSON returned!
        self.assertEqual(obj['points'], {"coordinates": [[-122.475233, 37.768616999999999], [-122.470416, 37.767381999999998]], "type": "MultiPoint"})

        # Or we can ask for XML
        connection.request('GET', '/api/v1/geonotes/4/', headers={'Accept': 'application/xml'})
        response = connection.getresponse()
        connection.close()

        self.assertEqual(response.status, 200)
        data = response.read()
        self.assertTrue('<points type="hash"><type>MultiPoint</type><coordinates type="list"><objects><value type="float">-122.475233</value><value type="float">37.768617</value></objects><objects><value type="float">-122.470416</value><value type="float">37.767382</value></objects></coordinates></points>' in data)
