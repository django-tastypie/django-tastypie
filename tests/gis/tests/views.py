from django.http import HttpRequest
from django.test import TestCase
from django.utils import simplejson as json


class ViewsTestCase(TestCase):
    def test_gets(self):
        resp = self.client.get('/api/v1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['geonotes'], {'list_endpoint': '/api/v1/geonotes/', 'schema': '/api/v1/geonotes/schema/'})

        resp = self.client.get('/api/v1/geonotes/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 3)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Points inside Golden Gate Park note', u'Golden Gate Park', u'Line inside Golden Gate Park'])

        resp = self.client.get('/api/v1/geonotes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 12)
        self.assertEqual(deserialized['title'], u'Points inside Golden Gate Park note')

        resp = self.client.get('/api/v1/geonotes/set/2;1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Golden Gate Park', u'Points inside Golden Gate Park note'])

    def test_posts(self):
        request = HttpRequest()
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        request._raw_post_data = post_data

        resp = self.client.post('/api/v1/geonotes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/geonotes/4/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/geonotes/4/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_puts(self):
        request = HttpRequest()
        post_data = '{"content": "Another new post.", "is_active": true, "title": "Another New Title", "slug": "new-title", "user": "/api/v1/users/1/", "lines": null, "points": null, "polys": null}'
        request._raw_post_data = post_data

        resp = self.client.put('/api/v1/geonotes/1/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)

        # make sure posted object exists
        resp = self.client.get('/api/v1/geonotes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['content'], 'Another new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_api_field_error(self):
        # When a field error is encountered, we should be presenting the message
        # back to the user.
        request = HttpRequest()
        post_data = '{"content": "More internet memes.", "is_active": true, "title": "IT\'S OVER 9000!", "slug": "its-over", "user": "/api/v1/users/9001/"}'
        request._raw_post_data = post_data

        resp = self.client.post('/api/v1/geonotes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, '{"error": "Could not find the provided object via resource URI \'/api/v1/users/9001/\'."}')

    def test_options(self):
        resp = self.client.options('/api/v1/geonotes/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/v1/geonotes/1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/v1/geonotes/schema/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/v1/geonotes/set/2;1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)
