from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest
from django.test import TestCase

try:
    import json
except ImportError:
    import simplejson as json

from basic.models import Note

class FilteringErrorsTestCase(TestCase):
    urls = 'validation.api.urls'
    
    def test_valid_date(self):
        resp = self.client.get('/api/v1/notes/', data={'format': 'json',
                                                      'created__gte':'2010-03-31'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized['objects']),
                         Note.objects.filter(created__gte='2010-03-31').count())
        

    def test_invalid_date(self):
        resp = self.client.get('/api/v1/notes/', data={
            'format': 'json', 'created__gte':'foo-baz-bar'})
        self.assertEqual(resp.status_code, 400)

    def test_create_note(self):
        # Correctly create a new note.
        post_data = '{"content": "A new note.", "user": "/api/v1/users/1/"}'
        resp = self.client.post('/api/v1/notes/', data=post_data,
                                content_type='application/json')
        self.assertEqual(resp.status_code, 201)

    def test_try_to_create_invalid_note(self):        
        # Create a note with more than 40 characters.
        post_data = '{"content": "%s", "user": "/api/v1/users/1/"}' % (
            'x' * 50, )
        resp = self.client.post('/api/v1/notes/', data=post_data,
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)

        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 1)
        self.assertEqual(deserialized.has_key('content'), True)

    def test_update_note(self):
        # Correctly update a new note.
        put_data = '{"content": "A new content."}'
        resp = self.client.put('/api/v1/notes/1/', data=put_data,
                                content_type='application/json')
        print "respuesta", resp.content
        self.assertEqual(resp.status_code, 204)

        resp = self.client.get('/api/v1/notes/1/',
                                content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        deserialized = json.loads(resp.content)
        self.assertEqual(deserialized.has_key('content'), True)
        self.assertEqual(deserialized['content'], "A new content.")

    def test_try_to_update_invalid_note(self):
        # Incorrectly update a new note.
        put_data = '{}'
        resp = self.client.put('/api/v1/notes/1/', data=put_data,
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)

        deserialized = json.loads(resp.content)
        self.assertEqual(deserialized.has_key('content'), True)
        self.assertEqual(deserialized['content'],
                         [u"We need the new content."])

        # Incorrectly update a new note.
        put_data = '{"content": "%s"}' % ('x' * 100, )
        resp = self.client.put('/api/v1/notes/1/', data=put_data,
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)

        deserialized = json.loads(resp.content)
        self.assertEqual(deserialized.has_key('content'), True)
        self.assertEqual(deserialized['content'],
                         [u"New content must be shorter."])
