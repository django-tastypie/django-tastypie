from django.http import HttpRequest
from django.test import TestCase
try:
    import json
except ImportError:
    import simplejson as json


class ViewsTestCase(TestCase):
    def test_gets(self):
        resp = self.client.get('/api/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 3)
        self.assertEqual(deserialized['notes'], {'list_endpoint': '/api/notes/', 'schema': '/api/notes/schema/'})

        resp = self.client.get('/api/notes/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'First Post!', u'Another Post'])

        resp = self.client.get('/api/notes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 10)
        self.assertEqual(deserialized['title'], u'First Post!')

        resp = self.client.get('/api/notes/set/2;1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Another Post', u'First Post!'])

    def test_posts(self):
        request = HttpRequest()
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/users/1/"}'
        request._raw_post_data = post_data

        resp = self.client.post('/api/notes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/notes/3/')

        # make sure posted object exists
        resp = self.client.get('/api/notes/3/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/users/1/')

    def test_puts(self):
        request = HttpRequest()
        post_data = '{"content": "Another new post.", "is_active": true, "title": "Another New Title", "slug": "new-title", "user": "/api/users/1/"}'
        request._raw_post_data = post_data

        resp = self.client.put('/api/notes/1/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)

        # make sure posted object exists
        resp = self.client.get('/api/notes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['content'], 'Another new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/users/1/')

    def test_api_field_error(self):
        # When a field error is encountered, we should be presenting the message
        # back to the user.
        request = HttpRequest()
        post_data = '{"content": "More internet memes.", "is_active": true, "title": "IT\'S OVER 9000!", "slug": "its-over", "user": "/api/users/9001/"}'
        request._raw_post_data = post_data

        resp = self.client.post('/api/notes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, "Could not find the provided object via resource URI '/api/users/9001/'.")


    def test_options(self):
        resp = self.client.options('/api/notes/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/notes/1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/notes/schema/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/notes/set/2;1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

