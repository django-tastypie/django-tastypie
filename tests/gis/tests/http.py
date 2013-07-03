import httplib
from urllib import quote
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
        data = json.loads(response.read())
        self.assertEqual(response.status, 200)
        self.assertEqual(data, {"geonotes": {"list_endpoint": "/api/v1/geonotes/", "schema": "/api/v1/geonotes/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}})

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
        data = json.loads(response.read())
        self.assertEqual(response.status, 200)
        self.assertEqual(len(data['objects']), 3)

        # Because floating point.
        self.assertEqual(data['objects'][0]['content'], "Wooo two points inside Golden Gate park")
        self.assertEqual(data['objects'][0]['points']['type'], 'MultiPoint')
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][0][0], -122.475233, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][0][1], 37.768616, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][1][0], -122.470416, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][1][1], 37.767381, places=5)

        self.assertEqual(data['objects'][1]['content'], "This is a note about Golden Gate Park. It contains Golden Gate Park\'s polygon")
        self.assertEqual(data['objects'][1]['polys']['type'], 'MultiPolygon')
        self.assertEqual(len(data['objects'][1]['polys']['coordinates']), 1)
        self.assertEqual(len(data['objects'][1]['polys']['coordinates'][0]), 1)
        self.assertEqual(len(data['objects'][1]['polys']['coordinates'][0][0]), 8)

        self.assertEqual(data['objects'][2]['content'], "A path inside Golden Gate Park! Huzzah!")
        self.assertEqual(data['objects'][2]['lines']['type'], 'MultiLineString')
        self.assertAlmostEqual(data['objects'][2]['lines']['coordinates'][0][0][0], -122.504544, places=5)
        self.assertAlmostEqual(data['objects'][2]['lines']['coordinates'][0][0][1], 37.767002, places=5)
        self.assertAlmostEqual(data['objects'][2]['lines']['coordinates'][0][1][0], -122.499995, places=5)
        self.assertAlmostEqual(data['objects'][2]['lines']['coordinates'][0][1][1], 37.768223, places=5)

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

    def test_filter_within(self):
        golden_gate_park_json = """{"type": "MultiPolygon", "coordinates": [[[[-122.511067, 37.771276], [-122.510037, 37.766391], [-122.510037, 37.763813], [-122.456822, 37.765848], [-122.452960, 37.766459], [-122.454848, 37.773990], [-122.475362, 37.773040], [-122.511067, 37.771276]]]]}"""

        # Get points
        connection = self.get_connection()
        connection.request('GET', '/api/v1/geonotes/?points__within=%s' % quote(golden_gate_park_json), headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)

        data = json.loads(response.read())
        # We get back the points inside Golden Gate park!
        self.assertEqual(data['objects'][0]['content'], "Wooo two points inside Golden Gate park")
        self.assertEqual(data['objects'][0]['points']['type'], 'MultiPoint')
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][0][0], -122.475233, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][0][1], 37.768616, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][1][0], -122.470416, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][1][1], 37.767381, places=5)

        # Get lines
        connection = self.get_connection()
        connection.request('GET', '/api/v1/geonotes/?lines__within=%s' % quote(golden_gate_park_json), headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)

        data = json.loads(response.read())
        # We get back the line inside Golden Gate park!
        self.assertEqual(data['objects'][0]['content'], "A path inside Golden Gate Park! Huzzah!")
        self.assertEqual(data['objects'][0]['lines']['type'], 'MultiLineString')
        self.assertAlmostEqual(data['objects'][0]['lines']['coordinates'][0][0][0], -122.504544, places=5)
        self.assertAlmostEqual(data['objects'][0]['lines']['coordinates'][0][0][1], 37.767002, places=5)
        self.assertAlmostEqual(data['objects'][0]['lines']['coordinates'][0][1][0], -122.499995, places=5)
        self.assertAlmostEqual(data['objects'][0]['lines']['coordinates'][0][1][1], 37.768223, places=5)

    def test_filter_contains(self):
        points_inside_golden_gate_park = """{"coordinates": [[-122.475233, 37.768616999999999], [-122.470416, 37.767381999999998]], "type": "MultiPoint"}"""

        # Get polys that contain the points
        connection = self.get_connection()
        connection.request('GET', '/api/v1/geonotes/?polys__contains=%s' % quote(points_inside_golden_gate_park), headers={'Accept': 'application/json'})
        response = connection.getresponse()
        connection.close()
        self.assertEqual(response.status, 200)

        data = json.loads(response.read())
        # We get back the golden gate park polygon!
        self.assertEqual(data['objects'][0]['content'], "This is a note about Golden Gate Park. It contains Golden Gate Park\'s polygon")
        self.assertEqual(data['objects'][0]['polys']['type'], 'MultiPolygon')
        self.assertEqual(len(data['objects'][0]['polys']['coordinates']), 1)
        self.assertEqual(len(data['objects'][0]['polys']['coordinates'][0]), 1)
        self.assertEqual(len(data['objects'][0]['polys']['coordinates'][0][0]), 8)
