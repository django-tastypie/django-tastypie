from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase, Client
from django.utils import simplejson as json


class ViewsTestCase(TestCase):
    def test_gets(self):
        resp = self.client.get('/api/v1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['notes'], {'list_endpoint': '/api/v1/notes/', 'schema': '/api/v1/notes/schema/'})

        resp = self.client.get('/api/v1/notes/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'First Post!', u'Another Post'])

        resp = self.client.get('/api/v1/notes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 9)
        self.assertEqual(deserialized['title'], u'First Post!')

        resp = self.client.get('/api/v1/notes/set/2;1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Another Post', u'First Post!'])

    def test_get_test_client_error(self):
        # The test server should re-raise exceptions to make debugging easier.
        self.assertRaises(Exception, self.client.get, '/api/v2/busted/', data={'format': 'json'})

    def test_posts(self):
        request = HttpRequest()
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        request._raw_post_data = post_data

        resp = self.client.post('/api/v1/notes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], 'http://testserver/api/v1/notes/3/')

        # make sure posted object exists
        resp = self.client.get('/api/v1/notes/3/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_puts(self):
        request = HttpRequest()
        post_data = '{"content": "Another new post.", "is_active": true, "title": "Another New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        request._raw_post_data = post_data

        resp = self.client.put('/api/v1/notes/1/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)

        # make sure posted object exists
        resp = self.client.get('/api/v1/notes/1/', data={'format': 'json'})
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

        resp = self.client.post('/api/v1/notes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, '{"error": "Could not find the provided object via resource URI \'/api/v1/users/9001/\'."}')

    def test_options(self):
        resp = self.client.options('/api/v1/notes/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/v1/notes/1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/v1/notes/schema/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

        resp = self.client.options('/api/v1/notes/set/2;1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content, allows)

    def test_slugbased(self):
        resp = self.client.get('/api/v2/slugbased/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'First Post', u'Another First Post'])

        resp = self.client.get('/api/v2/slugbased/first-post/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['title'], u'First Post')

        resp = self.client.get('/api/v2/slugbased/set/another-first-post;first-post/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Another First Post', u'First Post'])

    def test_session_auth(self):
        csrf_client = Client(enforce_csrf_checks=True)
        super_duper = User.objects.create_superuser('daniel', 'daniel@example.com', 'pass')

        # Unauthenticated.
        resp = csrf_client.get('/api/v2/sessionusers/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 401)

        # Now log in.
        self.assertTrue(csrf_client.login(username='daniel', password='pass'))
        # Fake the cookie the login didn't create. :(
        csrf_client.cookies['csrftoken'] = 'o9nXqnrypI9ydKoiWGCjDDcxXI7qRymH'

        resp = csrf_client.get('/api/v2/sessionusers/', data={'format': 'json'}, HTTP_X_CSRFTOKEN='o9nXqnrypI9ydKoiWGCjDDcxXI7qRymH')
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 2)
