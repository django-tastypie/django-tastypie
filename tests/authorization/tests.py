from django.test import TestCase
import json
from django.core.urlresolvers import reverse
from authorization.models import Note

import logging

logger = logging.getLogger(__name__)


class AuthTestCase(TestCase):
    fixtures = ['auth-test.json']

    def get_headers(self):
        return {
            'content_type': 'application/json',
        }

    def get_list_url(self, resource_name, api_name='v1'):
        list_url = reverse('api_dispatch_list', kwargs={
            'resource_name': resource_name,
            'api_name': api_name
            })
        return list_url

    def get_detail_url(self, resource_name, pk=1, api_name='v1'):
        detail_url = reverse('api_dispatch_detail', kwargs={
            'resource_name': resource_name,
            'api_name': api_name,
            'pk': pk
            })
        return detail_url

    def parse_response(self, resp, status_code=200):
        """
        Check status code and load json content
        """
        no_content = [
            405,
            404,
            401,
            204,
            201,
            202,
        ]
        self.assertEqual(resp.status_code, status_code, msg=resp.content)
        if resp.status_code in no_content:
            content = None
        else:
            try:
                content = json.loads(resp.content)
            except:
                content = "No JSON response could be decoded"
        return (resp, content)

    def test_note_perms(self):
        """
        Use the NoteResource api to test row level authorizations.
        """
        headers = self.get_headers()
        list_url = self.get_list_url(resource_name='notes')
        note = Note.objects.filter(user__username='testuser')[0]
        detail_url = self.get_detail_url(resource_name='notes', pk=note.pk)
        ## Anonymous User shouldn't access any notes.
        self.client.logout()
        resp, content = self.parse_response(self.client.get(list_url, **headers))
        self.assertEqual(content['meta']['total_count'], 0, msg="AnonymousUser should not have any notes.")
        resp, content = self.parse_response(
            self.client.get(detail_url, **headers),
            status_code=401)
        resp, content = self.parse_response(
            self.client.put(
                detail_url,
                data=json.dumps({'content': 'New content'}),
                **headers),
            status_code=401)
        resp, content = self.parse_response(
            self.client.post(list_url, **headers),
            status_code=401)
        resp, content = self.parse_response(
            self.client.delete(detail_url, **headers),
            status_code=401)

        ## Authenticated user
        self.client.login(username='testuser', password='secret')

        ## User can create notes, retrieve and modify their own.
        resp, content = self.parse_response(
            self.client.get(list_url, **headers))
        self.assertTrue(
            content['meta']['total_count'] > 0,
            msg="testuser could not retrieve their notes.")
        resp, content = self.parse_response(self.client.get(detail_url, **headers))
        resp, content = self.parse_response(
            self.client.put(
                detail_url,
                data=json.dumps({'content': 'New content for existing note.'}),
                **headers),
            status_code=204)
        resp, content = self.parse_response(
            self.client.delete(detail_url, **headers),
            status_code=204)
        resp, content = self.parse_response(
            self.client.post(
                list_url,
                data=json.dumps({'content': 'A brand new note!'}),
                **headers),
            status_code=201)

        ## User cannot retrieve or modify notes they don't own.
        other_note = Note.objects.filter(user__username='otheruser')[0]
        other_detail_url = self.get_detail_url(resource_name='notes', pk=other_note.pk)
        resp, content = self.parse_response(
            self.client.get(other_detail_url, **headers),
            status_code=401)
        resp, content = self.parse_response(
            self.client.put(other_detail_url, data=json.dumps({'title': 'bad title'}), **headers),
            status_code=401)
        resp, content = self.parse_response(
            self.client.delete(other_detail_url, **headers),
            status_code=401)
