import json

from django.test.utils import override_settings
from tastypie.exceptions import NotFound

from basic.models import Note
from testcases import TestCaseWithFixture
from django.test.testcases import SimpleTestCase


@override_settings(ROOT_URLCONF='validation.api.urls')
class FilteringErrorsTestCase(TestCaseWithFixture):
    def test_valid_date(self):
        resp = self.client.get('/api/v1/notes/', data={
            'format': 'json',
            'created__gte': '2010-03-31 00:00:00Z'
        })
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized['objects']), Note.objects.filter(created__gte='2010-03-31 00:00:00Z').count())

    def test_invalid_date(self):
        resp = self.client.get('/api/v1/notes/', data={
            'format': 'json',
            'created__gte': 'foo-baz-bar'
        })
        self.assertEqual(resp.status_code, 400)


@override_settings(ROOT_URLCONF='validation.api.urls')
class PostRelatedUrlValidationTestCase(TestCaseWithFixture):
    def test_valid_url(self):
        data_with_pk = json.dumps({
            'title': 'Test title related pk',
            'slug': 'test-slug-related-pk',
            'content': 'This is the content',
            'user': {'pk': 1},
        })
        data_with_url = json.dumps({
            'title': 'Test title related url',
            'slug': 'test-slug-related-url',
            'content': 'This is the content',
            'user': '/api/v1/users/1/',
        })
        resp_with_pk = self.client.post('/api/v1/notes/', data=data_with_pk, content_type='application/json')
        self.assertEqual(resp_with_pk.status_code, 201)
        note_posted_with_pk = json.loads(self.client.get(resp_with_pk['location']).content.decode('utf-8'))
        resp_with_url = self.client.post('/api/v1/notes/', data=data_with_url, content_type='application/json')
        self.assertEqual(resp_with_url.status_code, 201)
        note_posted_with_url = json.loads(self.client.get(resp_with_url['location']).content.decode('utf-8'))
        self.assertEqual(note_posted_with_pk['user'], note_posted_with_url['user'])

    def test_invalid_url(self):
        data = json.dumps({
            'title': 'Test title related url',
            'slug': 'test-slug-related-url',
            'content': 'This is the content',
            'user': 'invalid-url',
        })
        with self.assertRaises(NotFound):
            self.client.post('/api/v1/notes/', data=data, content_type='application/json')


@override_settings(ROOT_URLCONF='validation.api.urls')
class PostNestResouceValidationTestCase(TestCaseWithFixture):
    def test_valid_data(self):
        data = json.dumps({
            'title': 'Test Title',
            'slug': 'test-title',
            'content': 'This is the content',
            'user': {'pk': 1},  # loaded from fixtures
            'annotated': {'annotations': 'This is an annotations'},
        })

        resp = self.client.post('/api/v1/notes/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        note = json.loads(self.client.get(resp['location']).content.decode('utf-8'))
        self.assertTrue(note['annotated'])

    def test_invalid_data(self):
        data = json.dumps({
            'title': '',
            'slug': 'test-title',
            'content': 'This is the content',
            'user': {'pk': 1},  # loaded from fixtures
            'annotated': {'annotations': ''},
        })

        resp = self.client.post('/api/v1/notes/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'notes': {
                'title': ['This field is required.']
            },
            'annotated': {
                'annotations': ['This field is required.']
            }
        })


@override_settings(ROOT_URLCONF='validation.api.urls')
class PutDetailNestResouceValidationTestCase(TestCaseWithFixture):
    def test_valid_data(self):
        data = json.dumps({
            'title': 'Test Title',
            'slug': 'test-title',
            'content': 'This is the content',
            'annotated': {'annotations': 'This is another annotations'},
        })

        resp = self.client.put('/api/v1/notes/1/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)
        note = json.loads(self.client.get('/api/v1/notes/1/', content_type='application/json').content.decode('utf-8'))
        self.assertTrue(note['annotated'])
        self.assertEqual('test-title', note['slug'])

    def test_invalid_data(self):
        data = json.dumps({
            'title': '',
            'slug': '',
            'content': 'This is the content',
            'annotated': {'annotations': None},
        })

        resp = self.client.put('/api/v1/notes/1/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'notes': {
                'slug': ['This field is required.'],
                'title': ['This field is required.']
            },
            'annotated': {
                'annotations': ['This field is required.']
            }
        })


@override_settings(ROOT_URLCONF='validation.api.urls')
class PutListNestResouceValidationTestCase(TestCaseWithFixture):
    def test_valid_data(self):
        data = json.dumps({'objects': [
            {
                'id': 1,
                'title': 'Test Title',
                'slug': 'test-title',
                'content': 'This is the content',
                'annotated': {'annotations': 'This is another annotations'},
                'user': {'id': 1}
            },
            {
                'id': 2,
                'title': 'Test Title',
                'slug': 'test-title',
                'content': 'This is the content',
                'annotated': {'annotations': 'This is the third annotations'},
                'user': {'id': 1}
            }

        ]})

        resp = self.client.put('/api/v1/notes/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 204)
        note = json.loads(self.client.get('/api/v1/notes/1/', content_type='application/json').content.decode('utf-8'))
        self.assertTrue(note['annotated'])
        note = json.loads(self.client.get('/api/v1/notes/2/', content_type='application/json').content.decode('utf-8'))
        self.assertTrue(note['annotated'])

    def test_invalid_data(self):
        data = json.dumps({'objects': [
            {
                'id': 1,
                'title': 'Test Title',
                'slug': 'test-title',
                'annotated': {'annotations': None},
                'user': {'id': 1}
            },
            {
                'id': 2,
                'title': 'Test Title',
                'annotated': {'annotations': None},
                'user': {'id': 1}
            }
        ]})

        resp = self.client.put('/api/v1/notes/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'notes': {
                'content': ['This field is required.']
            },
            'annotated': {
                'annotations': ['This field is required.']
            }
        })


class TestJSONPValidation(SimpleTestCase):
    """
    Explicitly run the doctests for tastypie.utils.validate_jsonp
    """
    def test_jsonp(self):
        import tastypie.utils.validate_jsonp
        import doctest
        doctest.testmod(tastypie.utils.validate_jsonp)
