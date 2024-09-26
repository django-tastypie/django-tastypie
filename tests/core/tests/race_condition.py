# -*- coding: utf-8 -*-
import threading

from django.contrib.auth import get_user_model

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase, Client

from core.models import (
    Note
)

User = get_user_model()


class ApiConcurrentPatchTestCase(LiveServerTestCase):

    fixtures = ['note_testdata.json']

    def setUp(self):
        super(ApiConcurrentPatchTestCase, self).setUp()
        self.user = User.objects.get(username='johndoe')
        self.note = Note.objects.get(pk=1)
        self.client = Client()

    def test_concurrent_patch_requests(self):
        mapping_url = f"{self.live_server_url}{reverse('api_dispatch_detail', kwargs={'api_name': 'v1', 'resource_name': 'slownotes', 'pk': self.note.pk})}"

        response1 = self.client.patch(
            mapping_url, data={
                'title': 'original_title', 'slug': 'original_slug', 'content': 'original_content'
            }, content_type='application/json'
        )
        print(f"Concurrent PATCH request with HTTP status code: {response1.status_code}")
        self.assertEqual(response1.status_code, 202)  # 202 Accepted

        def patch_request(data):
            local_client = Client()
            response = local_client.patch(
                mapping_url,
                data=data,
                content_type='application/json'
            )
            print(f"Concurrent PATCH request with data {data} HTTP status code: {response.status_code}")

        # Define PATCH requests data
        data1 = {'title': 'new_title'}
        data2 = {'slug': 'new_slug'}
        data3 = {'content': 'new_content'}

        # Create threads to simulate concurrent requests
        thread1 = threading.Thread(target=patch_request, args=(data1,))
        thread2 = threading.Thread(target=patch_request, args=(data2,))
        thread3 = threading.Thread(target=patch_request, args=(data3,))

        # Start threads
        thread1.start()
        thread2.start()
        thread3.start()

        # Wait for threads to finish
        thread1.join()
        thread2.join()
        thread3.join()

        # Refresh the object from the database
        self.note.refresh_from_db()

        # Check final values (exact value check since race conditions should be handled)
        self.assertEqual(self.note.title, "new_title")
        self.assertEqual(self.note.slug, "new_slug")
        self.assertEqual(self.note.content, "new_content")
