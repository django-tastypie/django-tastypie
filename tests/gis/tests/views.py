import json

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from django.http import HttpRequest

from testcases import TestCaseWithFixture

from .utils import skipIfSpatialite


golden_gate_park_query = quote("""{"type": "MultiPolygon", "coordinates": [[[[-122.511067, 37.771276], [-122.510037, 37.766391], [-122.510037, 37.763813], [-122.456822, 37.765848], [-122.452960, 37.766459], [-122.454848, 37.773990], [-122.475362, 37.773040], [-122.511067, 37.771276]]]]}""")


class ViewsTestCase(TestCaseWithFixture):
    def test_gets(self):
        resp = self.client.get('/api/v1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['geonotes'], {'list_endpoint': '/api/v1/geonotes/', 'schema': '/api/v1/geonotes/schema/'})

        resp = self.client.get('/api/v1/geonotes/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 3)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Points inside Golden Gate Park note', u'Golden Gate Park', u'Line inside Golden Gate Park'])

        resp = self.client.get('/api/v1/geonotes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 12)
        self.assertEqual(deserialized['title'], u'Points inside Golden Gate Park note')

        resp = self.client.get('/api/v1/geonotes/set/2;1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Golden Gate Park', u'Points inside Golden Gate Park note'])

    def test_posts(self):
        request = HttpRequest()
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        request._body = request._raw_post_data = post_data

        resp = self.client.post('/api/v1/geonotes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp['location'].endswith('/api/v1/geonotes/4/'))

        # make sure posted object exists
        resp = self.client.get('/api/v1/geonotes/4/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_puts(self):
        request = HttpRequest()
        post_data = '{"content": "Another new post.", "is_active": true, "title": "Another New Title", "slug": "new-title", "user": "/api/v1/users/1/", "lines": null, "points": null, "polys": null}'
        request._body = request._raw_post_data = post_data

        resp = self.client.put('/api/v1/geonotes/1/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)

        # make sure posted object exists
        resp = self.client.get('/api/v1/geonotes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['content'], 'Another new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_api_field_error(self):
        # When a field error is encountered, we should be presenting the message
        # back to the user.
        request = HttpRequest()
        post_data = '{"content": "More internet memes.", "is_active": true, "title": "IT\'S OVER 9000!", "slug": "its-over", "user": "/api/v1/users/9001/"}'
        request._body = request._raw_post_data = post_data

        resp = self.client.post('/api/v1/geonotes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), '{"error": "Could not find the provided users object via resource URI \'/api/v1/users/9001/\'."}')

    def test_options(self):
        resp = self.client.options('/api/v1/geonotes/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content.decode('utf-8'), allows)

        resp = self.client.options('/api/v1/geonotes/1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content.decode('utf-8'), allows)

        resp = self.client.options('/api/v1/geonotes/schema/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content.decode('utf-8'), allows)

        resp = self.client.options('/api/v1/geonotes/set/2;1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content.decode('utf-8'), allows)


class MoreViewsTestCase(TestCaseWithFixture):
    def test_get_apis_json(self):
        response = self.client.get('/api/v1/', HTTP_ACCEPT='application/json')
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"geonotes": {"list_endpoint": "/api/v1/geonotes/", "schema": "/api/v1/geonotes/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}})

    def test_get_apis_xml(self):
        response = self.client.get('/api/v1/', HTTP_ACCEPT='application/xml')
        data = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><geonotes type="hash"><list_endpoint>/api/v1/geonotes/</list_endpoint><schema>/api/v1/geonotes/schema/</schema></geonotes><users type="hash"><list_endpoint>/api/v1/users/</list_endpoint><schema>/api/v1/users/schema/</schema></users></response>')

    def test_get_list(self):
        response = self.client.get('/api/v1/geonotes/', HTTP_ACCEPT='application/json')
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
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
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        response = self.client.post('/api/v1/geonotes/', data=post_data, HTTP_ACCEPT='application/json', content_type='application/json')

        self.assertEqual(response.status_code, 201)

        location = response['Location']
        self.assertTrue(location.endswith('/api/v1/geonotes/4/'))

        # make sure posted object exists
        response = self.client.get('/api/v1/geonotes/4/', HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)

        data = response.content.decode('utf-8')
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_post_geojson(self):
        post_data = """{
            "content": "A new post.", "is_active": true, "title": "New Title2",
            "slug": "new-title2", "user": "/api/v1/users/1/",
            "polys": { "type": "MultiPolygon", "coordinates": [ [ [ [ -122.511067, 37.771276 ], [ -122.510037, 37.766391 ], [ -122.510037, 37.763813 ], [ -122.456822, 37.765848 ], [ -122.452960, 37.766459 ], [ -122.454848, 37.773990 ], [ -122.475362, 37.773040 ], [ -122.511067, 37.771276 ] ] ] ] }
        }"""
        response = self.client.post('/api/v1/geonotes/', data=post_data, HTTP_ACCEPT='application/json', content_type='application/json')

        self.assertEqual(response.status_code, 201)

        location = response['Location']
        self.assertTrue(location.endswith('/api/v1/geonotes/4/'))

        # make sure posted object exists
        response = self.client.get('/api/v1/geonotes/4/', HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)

        data = response.content.decode('utf-8')
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')
        self.assertEqual(obj['polys'], {u'type': u'MultiPolygon', u'coordinates': [[[[-122.511067, 37.771276], [-122.510037, 37.766390999999999], [-122.510037, 37.763812999999999], [-122.456822, 37.765847999999998], [-122.45296, 37.766458999999998], [-122.454848, 37.773989999999998], [-122.475362, 37.773040000000002], [-122.511067, 37.771276]]]]})

    def test_post_xml(self):
        post_data = """<object><created>2010-03-30T20:05:00</created><polys type="null"/><is_active type="boolean">True</is_active><title>Points inside Golden Gate Park note 2</title><lines type="null"/><slug>points-inside-golden-gate-park-note-2</slug><content>A new post.</content><points type="hash"><type>MultiPoint</type><coordinates type="list"><objects><value type="float">-122.475233</value><value type="float">37.768617</value></objects><objects><value type="float">-122.470416</value><value type="float">37.767382</value></objects></coordinates></points><user>/api/v1/users/1/</user></object>"""
        response = self.client.post('/api/v1/geonotes/', data=post_data, HTTP_ACCEPT='application/xml', content_type='application/xml')

        self.assertEqual(response.status_code, 201)

        location = response['Location']
        self.assertTrue(location.endswith('/api/v1/geonotes/4/'))

        # make sure posted object exists
        response = self.client.get('/api/v1/geonotes/4/', HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)

        data = response.content.decode('utf-8')
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')
        # Weeeee!  GeoJSON returned!
        self.assertEqual(obj['points'], {"coordinates": [[-122.475233, 37.768616999999999], [-122.470416, 37.767381999999998]], "type": "MultiPoint"})

        # Or we can ask for XML
        response = self.client.get('/api/v1/geonotes/4/', HTTP_ACCEPT='application/xml')

        self.assertEqual(response.status_code, 200)
        data = response.content.decode('utf-8')

        self.assertIn('<points type="hash"><coordinates type="list"><objects><value type="float">-122.475233</value><value type="float">37.768617</value></objects><objects><value type="float">-122.470416</value><value type="float">37.767382</value></objects></coordinates><type>MultiPoint</type></points>', data)

    def test_filter_within_on_points(self):

        # Get points
        response = self.client.get('/api/v1/geonotes/?points__within=%s' % golden_gate_park_query, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content.decode('utf-8'))
        # We get back the points inside Golden Gate park!
        self.assertEqual(data['objects'][0]['content'], "Wooo two points inside Golden Gate park")
        self.assertEqual(data['objects'][0]['points']['type'], 'MultiPoint')
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][0][0], -122.475233, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][0][1], 37.768616, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][1][0], -122.470416, places=5)
        self.assertAlmostEqual(data['objects'][0]['points']['coordinates'][1][1], 37.767381, places=5)

    @skipIfSpatialite
    def test_filter_within_on_lines(self):

        # Get lines
        response = self.client.get('/api/v1/geonotes/?lines__within=%s' % golden_gate_park_query, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content.decode('utf-8'))
        # We get back the line inside Golden Gate park!
        self.assertEqual(data['objects'][0]['content'], "A path inside Golden Gate Park! Huzzah!")
        self.assertEqual(data['objects'][0]['lines']['type'], 'MultiLineString')
        self.assertAlmostEqual(data['objects'][0]['lines']['coordinates'][0][0][0], -122.504544, places=5)
        self.assertAlmostEqual(data['objects'][0]['lines']['coordinates'][0][0][1], 37.767002, places=5)
        self.assertAlmostEqual(data['objects'][0]['lines']['coordinates'][0][1][0], -122.499995, places=5)
        self.assertAlmostEqual(data['objects'][0]['lines']['coordinates'][0][1][1], 37.768223, places=5)

    @skipIfSpatialite
    def test_filter_contains(self):
        points_inside_golden_gate_park = """{"coordinates": [[-122.475233, 37.768616999999999], [-122.470416, 37.767381999999998]], "type": "MultiPoint"}"""

        # Get polys that contain the points
        response = self.client.get('/api/v1/geonotes/?polys__contains=%s' % quote(points_inside_golden_gate_park), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content.decode('utf-8'))
        # We get back the golden gate park polygon!
        self.assertEqual(data['objects'][0]['content'], "This is a note about Golden Gate Park. It contains Golden Gate Park\'s polygon")
        self.assertEqual(data['objects'][0]['polys']['type'], 'MultiPolygon')
        self.assertEqual(len(data['objects'][0]['polys']['coordinates']), 1)
        self.assertEqual(len(data['objects'][0]['polys']['coordinates'][0]), 1)
        self.assertEqual(len(data['objects'][0]['polys']['coordinates'][0][0]), 8)
