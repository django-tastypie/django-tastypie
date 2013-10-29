# encoding: utf-8
from __future__ import absolute_import

from django.test import TestCase
from django.utils import simplejson


class RelatedResourceTestCase(TestCase):
    def _validate_post_detail_json(self, json):
        data = simplejson.loads(json)

        self.assertEqual(3, len(data['comments']))
        self.assertIn('/api/v1/comments/1/', data['comments'])
        self.assertEqual(data['user'], '/api/v1/users/1/')

    def test_optimized_light_related_fields(self):
        # We expect 2 queries total due to select_related + prefetch_related
        # + 1 for the post and user FL
        # + 1 for all the comments

        with self.assertNumQueries(2):
            resp = self.client.get("/api/v1/posts_optimized/1/")
        self._validate_post_detail_json(resp.content)

    def test_default_light_related_fields(self):
        # We expect 4 queries total:
        # + 1 for the post
        # + 1 for the user
        # + 1 for the content type
        # + 1 for the comments

        with self.assertNumQueries(4):
            resp = self.client.get("/api/v1/posts/1/")

        self._validate_post_detail_json(resp.content)
