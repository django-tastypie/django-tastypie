from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest
from django.test import TestCase
import django

if django.get_version() < '1.2':
    import monkeypatch_django_test_put

settings.DEBUG = True
try:
    import json
except ImportError:
    import simplejson as json

from basic.models import Note

# class FilteringErrorsTestCase(TestCase):
#     urls = 'validation.api.urls'

#     def test_valid_date(self):
#         resp = self.client.get('/api/v1/notes/', data={'format': 'json',
#                                                       'created__gte':'2010-03-31'})
#         self.assertEqual(resp.status_code, 200)
#         deserialized = json.loads(resp.content)
#         self.assertEqual(len(deserialized['objects']),
#                          Note.objects.filter(created__gte='2010-03-31').count())


#     def test_invalid_date(self):
#         resp = self.client.get('/api/v1/notes/', data={'format': 'json',
#                                                       'created__gte':'foo-baz-bar'})
#         self.assertEqual(resp.status_code, 400)

class PostNestResouceValidationTestCase(TestCase):
    urls = 'validation.api.urls'

    def test_valid_data(self):
        data = json.dumps({
            'title' : 'Test Title',
            'slug' : 'test-title',
            'content' : 'This is the content',
            'user' : {'pk' : 1}, # loaded from fixtures
            'annotated_note' : {'annotations' : 'This is an annotations'},
        })

        resp = self.client.post('/api/v1/notes/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        note = json.loads(self.client.get(resp['location']).content)
        self.assertTrue(note['annotated_note'])

    def test_invalid_data(self):
        data = json.dumps({
            'title' : '',
            'slug' : 'test-title',
            'content' : 'This is the content',
            'user' : {'pk' : 1}, # loaded from fixtures
            'annotated_note' : {'annotations' : ''},
        })

        resp = self.client.post('/api/v1/notes/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(set(['title', 'annotated_note']), set(json.loads(resp.content).keys()))


class PutDetailNestResouceValidationTestCase(TestCase):
    urls = 'validation.api.urls'

    def test_valid_data(self):
        data = json.dumps({
            'title' : 'Test Title',
            'slug' : 'test-title',
            'content' : 'This is the content',
            'annotated_note' : {'annotations' : 'This is another annotations'},
        })

        resp = self.client.put('/api/v1/notes/1/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)
        note = json.loads(self.client.get('/api/v1/notes/1/', content_type='application/json').content)
        self.assertTrue(note['annotated_note'])

    def test_invalid_data(self):
        data = json.dumps({
            'title' : '',
            'slug' : '',
            'content' : 'This is the content',
            'annotated_note' : {'annotations' : None},
        })

        resp = self.client.put('/api/v1/notes/1/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(set(['title', 'annotated_note', 'slug']), set(json.loads(resp.content).keys()))


class PutListNestResouceValidationTestCase(TestCase):
    urls = 'validation.api.urls'

    def test_valid_data(self):
        data = json.dumps({'objects' : [
            {
                'pk' : 1,
                'title' : 'Test Title',
                'slug' : 'test-title',
                'content' : 'This is the content',
                'annotated_note' : {'annotations' : 'This is another annotations'},
                'user' : {'pk' : 1}
            },
            {
                'pk' : 2,
                'title' : 'Test Title',
                'slug' : 'test-title',
                'content' : 'This is the content',
                'annotated_note' : {'annotations' : 'This is the third annotations'},
                'user' : {'pk' : 1}
            }

        ]})

        resp = self.client.put('/api/v1/notes/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)
        note = json.loads(self.client.get('/api/v1/notes/1/', content_type='application/json').content)
        self.assertTrue(note['annotated_note'])
        note = json.loads(self.client.get('/api/v1/notes/2/', content_type='application/json').content)
        self.assertTrue(note['annotated_note'])

    # def test_invalid_data(self):
    #     # FIXME: Should show errors for all.
    #     data = json.dumps({'objects' : [
    #         {
    #             'pk' : 1,
    #             'title' : 'Test Title',
    #             'slug' : 'test-title',
    #             'annotated_note' : {'annotations' : None},
    #             'user' : {'pk' : 1}
    #         },
    #         {
    #             'pk' : 2,
    #             'title' : 'Test Title',
    #             'annotated_note' : {'annotations' : None},
    #             'user' : {'pk' : 1}
    #         }
    #     ]})

    #     resp = self.client.put('/api/v1/notes/', data=data, content_type='application/json')
    #     self.assertEqual(resp.status_code, 400)
    #     self.assertEqual(set(['content', 'annotated_note']), set(json.loads(resp.content).keys()))
