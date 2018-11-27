import json

from django.contrib.auth.models import User
from django.test import Client
from django.test.utils import override_settings

from testcases import TestCaseWithFixture


class ViewsTestCase(TestCaseWithFixture):
    def test_gets(self):
        resp = self.client.get('/api/v1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 6)
        self.assertEqual(deserialized['notes'], {'list_endpoint': '/api/v1/notes/', 'schema': '/api/v1/notes/schema/'})

        resp = self.client.get('/api/v1/notes/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'First Post!', u'Another Post'])

        resp = self.client.get('/api/v1/notes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 9)
        self.assertEqual(deserialized['title'], u'First Post!')

        resp = self.client.get('/api/v1/notes/set/2;1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Another Post', u'First Post!'])

    def test_get_test_client_error(self):
        # The test server should re-raise exceptions to make debugging easier.
        self.assertRaises(Exception, self.client.get, '/api/v2/busted/', data={'format': 'json'})

    def test_posts(self):
        post_data = b'{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'

        resp = self.client.post('/api/v1/notes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp['location'].endswith('/api/v1/notes/3/'))

        # make sure posted object exists
        resp = self.client.get('/api/v1/notes/3/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_puts(self):
        post_data = '{"content": "Another new post.", "is_active": true, "title": "Another New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'

        resp = self.client.put('/api/v1/notes/1/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)

        # make sure posted object exists
        resp = self.client.get('/api/v1/notes/1/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(obj['content'], 'Another new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_api_field_error(self):
        # When a field error is encountered, we should be presenting the message
        # back to the user.
        post_data = '{"content": "More internet memes.", "is_active": true, "title": "IT\'S OVER 9000!", "slug": "its-over", "user": "/api/v1/users/9001/"}'

        resp = self.client.post('/api/v1/notes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            json.loads(resp.content.decode('utf-8')),
            {
                "error": "Could not find the provided users object via resource URI \'/api/v1/users/9001/\'."
            }
        )

    def test_invalid_json_error(self):
        # When the given data is not valid JSON a readable error message should be returned.
        post_data = '{"content": "More internet memes.", "is_active": true, "title": "IT\'S OVER 9000!", "slug": "its-over",'

        resp = self.client.post('/api/v1/notes/', data=post_data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            json.loads(resp.content.decode('utf-8')),
            {
                "error": "Request is not valid JSON."
            }
        )

    def test_options(self):
        resp = self.client.options('/api/v1/notes/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content.decode('utf-8'), allows)

        resp = self.client.options('/api/v1/notes/1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET,POST,PUT,DELETE,PATCH'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content.decode('utf-8'), allows)

        resp = self.client.options('/api/v1/notes/schema/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content.decode('utf-8'), allows)

        resp = self.client.options('/api/v1/notes/set/2;1/')
        self.assertEqual(resp.status_code, 200)
        allows = 'GET'
        self.assertEqual(resp['Allow'], allows)
        self.assertEqual(resp.content.decode('utf-8'), allows)

    def test_slugbased(self):
        resp = self.client.get('/api/v2/slugbased/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(deserialized['meta']['limit'], 20)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'First Post', u'Another First Post'])

        resp = self.client.get('/api/v2/slugbased/first-post/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['title'], u'First Post')

        resp = self.client.get('/api/v2/slugbased/set/another-first-post;first-post/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(len(deserialized['objects']), 2)
        self.assertEqual([obj['title'] for obj in deserialized['objects']], [u'Another First Post', u'First Post'])

    def test_session_auth(self):
        csrf_client = Client(enforce_csrf_checks=True)
        User.objects.create_superuser('daniel', 'daniel@example.com', 'pass')

        # Unauthenticated.
        resp = csrf_client.get('/api/v2/sessionusers/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 401)

        # Now log in.
        self.assertTrue(csrf_client.login(username='daniel', password='pass'))
        # Fake the cookie the login didn't create. :(
        csrf_client.cookies['csrftoken'] = 'o9nXqnrypI9ydKoiWGCjDDcxXI7qRymH'

        resp = csrf_client.get('/api/v2/sessionusers/', data={'format': 'json'}, HTTP_X_CSRFTOKEN='o9nXqnrypI9ydKoiWGCjDDcxXI7qRymH')
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 2)


@override_settings(DEBUG=True)
class MoreViewsTestCase(TestCaseWithFixture):
    def test_get_apis_json(self):
        response = self.client.get('/api/v1/', HTTP_ACCEPT='application/json')
        data = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, '{"cache_disabled_users": {"list_endpoint": "/api/v1/cache_disabled_users/", "schema": "/api/v1/cache_disabled_users/schema/"}, "cached_users": {"list_endpoint": "/api/v1/cached_users/", "schema": "/api/v1/cached_users/schema/"}, "notes": {"list_endpoint": "/api/v1/notes/", "schema": "/api/v1/notes/schema/"}, "private_cached_users": {"list_endpoint": "/api/v1/private_cached_users/", "schema": "/api/v1/private_cached_users/schema/"}, "public_cached_users": {"list_endpoint": "/api/v1/public_cached_users/", "schema": "/api/v1/public_cached_users/schema/"}, "users": {"list_endpoint": "/api/v1/users/", "schema": "/api/v1/users/schema/"}}')

    def test_get_apis_invalid_accept(self):
        response = self.client.get('/api/v1/', HTTP_ACCEPT='invalid')
        self.assertEqual(response.status_code, 400, "Invalid HTTP Accept headers should return HTTP 400")

    def test_get_resource_invalid_accept(self):
        """Invalid HTTP Accept headers should return HTTP 400"""
        # We need to test this twice as there's a separate dispatch path for resources:

        response = self.client.get('/api/v1/notes/', HTTP_ACCEPT='invalid')
        self.assertEqual(response.status_code, 400, "Invalid HTTP Accept headers should return HTTP 400")

    def test_get_apis_xml(self):
        response = self.client.get('/api/v1/', HTTP_ACCEPT='application/xml')
        data = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><cache_disabled_users type="hash"><list_endpoint>/api/v1/cache_disabled_users/</list_endpoint><schema>/api/v1/cache_disabled_users/schema/</schema></cache_disabled_users><cached_users type="hash"><list_endpoint>/api/v1/cached_users/</list_endpoint><schema>/api/v1/cached_users/schema/</schema></cached_users><notes type="hash"><list_endpoint>/api/v1/notes/</list_endpoint><schema>/api/v1/notes/schema/</schema></notes><private_cached_users type="hash"><list_endpoint>/api/v1/private_cached_users/</list_endpoint><schema>/api/v1/private_cached_users/schema/</schema></private_cached_users><public_cached_users type="hash"><list_endpoint>/api/v1/public_cached_users/</list_endpoint><schema>/api/v1/public_cached_users/schema/</schema></public_cached_users><users type="hash"><list_endpoint>/api/v1/users/</list_endpoint><schema>/api/v1/users/schema/</schema></users></response>')

    def test_get_list(self):
        response = self.client.get('/api/v1/notes/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 2}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00", "user": "/api/v1/users/1/"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00", "user": "/api/v1/users/1/"}]}')

    def test_post_object(self):
        post_data = '{"content": "A new post.", "is_active": true, "title": "New Title", "slug": "new-title", "user": "/api/v1/users/1/"}'
        response = self.client.post('/api/v1/notes/', data=post_data, HTTP_ACCEPT='application/json', content_type='application/json')
        self.assertEqual(response.status_code, 201)
        location = response['Location']
        self.assertTrue(location.endswith('/api/v1/notes/3/'))

        # make sure posted object exists
        response = self.client.get('/api/v1/notes/3/', HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)

        data = response.content.decode('utf-8')
        obj = json.loads(data)

        self.assertEqual(obj['content'], 'A new post.')
        self.assertEqual(obj['is_active'], True)
        self.assertEqual(obj['user'], '/api/v1/users/1/')

    def test_vary_accept(self):
        """
        Ensure that resources return the Vary: Accept header.
        """
        response = self.client.get('/api/v1/cached_users/', HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)

        vary = response['Vary']
        vary_types = [x.strip().lower() for x in vary.split(",") if x.strip()]
        self.assertIn("accept", vary_types)

    def test_cache_control(self):
        response = self.client.get('/api/v1/cached_users/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        cache_control = set([x.strip().lower() for x in response["Cache-Control"].split(",") if x.strip()])

        self.assertEqual(cache_control, set(["s-maxage=3600", "max-age=3600"]))
        self.assertTrue('"johndoe"' in response.content.decode('utf-8'))

    def test_cache_disabled_control(self):
        response = self.client.get('/api/v1/cache_disabled_users/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        cache_control = set([x.strip().lower() for x in response["Cache-Control"].split(",") if x.strip()])

        self.assertEqual(cache_control, set(["s-maxage=0", "max-age=0"]))
        self.assertTrue('"johndoe"' in response.content.decode('utf-8'))

    def test_public_cache_control(self):
        response = self.client.get('/api/v1/public_cached_users/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        cache_control = set([x.strip().lower() for x in response["Cache-Control"].split(",") if x.strip()])

        self.assertEqual(cache_control, set(["s-maxage=3600", "max-age=3600", "public"]))
        self.assertTrue('"johndoe"' in response.content.decode('utf-8'))

    def test_private_cache_control(self):
        response = self.client.get('/api/v1/private_cached_users/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        cache_control = set([x.strip().lower() for x in response["Cache-Control"].split(",") if x.strip()])

        self.assertEqual(cache_control, set(["s-maxage=3600", "max-age=3600", "private"]))
        self.assertTrue('"johndoe"' in response.content.decode('utf-8'))
