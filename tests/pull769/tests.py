from django.test.testcases import TestCase
from django.test.client import Client
from django.utils import simplejson as json
from django.http import HttpResponseBadRequest


class Pull769TestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_post_for_blank_false_field_with_name_coincident_to_model_field_name(self):
        response = self.client.post(
            '/v1/related/',
            json.dumps({'name': 'test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content,
            "The 'simple' field has no data and doesn't allow a default or null value."
        )
