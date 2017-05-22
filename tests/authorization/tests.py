import json
import mock

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from tastypie.test import ResourceTestCaseMixin
from .models import AuthorProfile, Article
from .api.resources import PerUserAuthorization


# If `./run_all_tests.sh authorization` is run, ret_false might never get called
# and some tests will fail, but if `./run_all_tests.sh authorization.tests` is
# run they'll pass.
def ret_false(*args):
    return False


class PerUserAuthorizationTestCase(ResourceTestCaseMixin, TestCase):
    def setUp(self):
        super(PerUserAuthorizationTestCase, self).setUp()

        # Make some data.
        self.site_1 = Site.objects.create(
            domain='superawesomenewssite.com',
            name='Super Awesome News Site'
        )
        self.site_2 = Site.objects.create(
            domain='snarkynewssite.com',
            name='Snarky News Site'
        )

        self.user_1 = User.objects.create_user('mr_author', 'mister_author@example.com', 'pass')
        self.user_2 = User.objects.create_user('mrs_author', 'missus_author@example.com', 'pass')
        self.user_3 = User.objects.create_user('ms_editor', 'miss_editor@example.com', 'pass')

        self.author_profile_1 = AuthorProfile.objects.create(
            user=self.user_1,
            short_bio="Just a dude writing stories for Super Awesome.",
            bio="Just a dude writing stories for Super Awesome. Life is good."
        )
        self.author_profile_2 = AuthorProfile.objects.create(
            user=self.user_2,
            short_bio="A highly professional woman writing for Snarky.",
            bio="Way better educated than that schmuck writing for Super Awesome. <scoff />"
        )
        self.author_profile_3 = AuthorProfile.objects.create(
            user=self.user_3,
            short_bio="I wish my writers used spellcheck.",
            bio="Whatever."
        )
        self.author_profile_1.sites.add(self.site_1)
        self.author_profile_2.sites.add(self.site_2)
        self.author_profile_3.sites.add(self.site_1, self.site_2)

        self.article_1 = Article.objects.create(
            title='New Stuff Announced Today!',
            content="Some big tech company announced new stuffs! Go get your consumerism on!"
        )
        self.article_1.authors.add(self.author_profile_1, self.author_profile_3)

        self.article_2 = Article.objects.create(
            title='Editorial: Why stuff is great',
            content="Because you can buy buy buy & fill the gaping voids in your life."
        )
        self.article_2.authors.add(self.author_profile_3)

        self.article_3 = Article.objects.create(
            title='Ugh, Who Cares About New Stuff?',
            content="Obviously stuff by other by other company is way better."
        )
        self.article_3.authors.add(self.author_profile_2, self.author_profile_3)

        # Auth bits.
        self.author_auth_1 = self.create_basic('mr_author', 'pass')
        self.author_auth_2 = self.create_basic('mrs_author', 'pass')
        self.author_auth_3 = self.create_basic('ms_editor', 'pass')

        # URIs.
        self.article_uri_1 = '/api/v1/article/{0}/'.format(self.article_1.pk)
        self.article_uri_2 = '/api/v1/article/{0}/'.format(self.article_2.pk)
        self.article_uri_3 = '/api/v1/article/{0}/'.format(self.article_3.pk)
        self.author_uri_1 = '/api/v1/authorprofile/{0}/'.format(self.author_profile_1.pk)
        self.author_uri_2 = '/api/v1/authorprofile/{0}/'.format(self.author_profile_2.pk)
        self.author_uri_3 = '/api/v1/authorprofile/{0}/'.format(self.author_profile_3.pk)

    def test_get_list(self):
        # Should be all articles.
        resp = self.api_client.get('/api/v1/article/', format='json', authentication=self.author_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)
        first_article = self.deserialize(resp)['objects'][0]
        self.assertEqual(first_article['id'], self.article_1.pk)
        self.assertEqual(len(first_article['authors']), 2)

        # Should ALSO be all articles.
        resp = self.api_client.get('/api/v1/article/', format='json', authentication=self.author_auth_2)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)
        first_article = self.deserialize(resp)['objects'][0]
        self.assertEqual(first_article['id'], self.article_1.pk)
        self.assertEqual(len(first_article['authors']), 2)

    def test_get_detail(self):
        # Should be all articles.
        resp = self.api_client.get(self.article_uri_1, format='json', authentication=self.author_auth_1)
        self.assertValidJSONResponse(resp)
        first_article = self.deserialize(resp)
        self.assertKeys(first_article, ['added_on', 'authors', 'content', 'id', 'resource_uri', 'slug', 'title'])
        self.assertEqual(first_article['id'], self.article_1.pk)

        # Should ALSO be all articles, even though it's not our article.
        resp = self.api_client.get(self.article_uri_1, format='json', authentication=self.author_auth_2)
        self.assertValidJSONResponse(resp)
        first_article = self.deserialize(resp)
        self.assertKeys(first_article, ['added_on', 'authors', 'content', 'id', 'resource_uri', 'slug', 'title'])
        self.assertEqual(first_article['id'], self.article_1.pk)

        # Should ALSO ALSO be all articles, even though it's not our article.
        resp = self.api_client.get(self.article_uri_2, format='json', authentication=self.author_auth_1)
        self.assertValidJSONResponse(resp)
        second_article = self.deserialize(resp)
        self.assertKeys(second_article, ['added_on', 'authors', 'content', 'id', 'resource_uri', 'slug', 'title'])
        self.assertEqual(second_article['id'], self.article_2.pk)

    @mock.patch.object(PerUserAuthorization, "read_detail", ret_false)
    def test_get_unauthorized_detail(self):
        resp = self.api_client.get(self.article_uri_1, format='json', authentication=self.author_auth_1)
        self.assertHttpUnauthorized(resp)

    def test_post_list(self):
        # Should be able to create with reckless abandon.
        self.assertEqual(Article.objects.count(), 3)
        self.assertHttpCreated(self.api_client.post('/api/v1/article/', format='json', data={
            'title': 'Yet Another Story',
            'content': 'Stuff.',
            'authors': [self.author_uri_1],
        }, authentication=self.author_auth_1))
        # Verify a new one has been added.
        self.assertEqual(Article.objects.count(), 4)

        # Should ALSO be able to create with reckless abandon.
        self.assertHttpCreated(self.api_client.post('/api/v1/article/', format='json', data={
            'title': 'Even Another Story',
            'content': 'This time, with competent words.',
            'authors': [self.author_uri_2],
        }, authentication=self.author_auth_2))
        # Verify a new one has been added.
        self.assertEqual(Article.objects.count(), 5)

    @mock.patch.object(PerUserAuthorization, "create_detail", ret_false)
    def test_post_unauthorized_detail(self):
        resp = self.api_client.post('/api/v1/article/', format='json', data={
            'title': 'Yet Another Story',
            'content': 'Stuff.',
            'authors': [self.author_uri_1],
        }, authentication=self.author_auth_1)
        self.assertHttpUnauthorized(resp)

    def test_put_list(self):
        resp = self.api_client.get('/api/v1/article/', format='json', authentication=self.author_auth_2)
        self.assertHttpOK(resp)
        the_data = json.loads(resp.content.decode('utf-8'))

        # Tweak the data.
        the_data['objects'][0]['title'] = 'This is edited.'
        the_data['objects'][2]['title'] = 'Updated: {0}'.format(the_data['objects'][2]['title'])

        # Editor can edit whatever, since they're on all the articles.
        self.assertEqual(Article.objects.count(), 3)
        self.assertHttpAccepted(self.api_client.put('/api/v1/article/', format='json', data=the_data, authentication=self.author_auth_3))
        # Verify no change in count.
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Article.objects.get(pk=self.article_1.pk).title, 'This is edited.')
        self.assertEqual(Article.objects.get(pk=self.article_1.pk).content, 'Some big tech company announced new stuffs! Go get your consumerism on!')
        self.assertEqual(Article.objects.get(pk=self.article_3.pk).title, 'Updated: Ugh, Who Cares About New Stuff?')
        self.assertEqual(Article.objects.get(pk=self.article_3.pk).content, 'Obviously stuff by other by other company is way better.')

        # But a regular author can't update the whole list.
        the_data['objects'][2]['title'] = "Your Story Is Bad And You Should Feel Bad"
        del the_data['objects'][0]
        self.assertHttpUnauthorized(self.api_client.put('/api/v1/article/', format='json', data=the_data, authentication=self.author_auth_1))
        # Verify count goes down.
        self.assertEqual(Article.objects.count(), 2)
        # Verify he couldn't edit that title.
        self.assertEqual(Article.objects.get(pk=self.article_3.pk).title, 'Updated: Ugh, Who Cares About New Stuff?')

    def test_put_detail(self):
        # Should be able to update our story.
        self.assertEqual(Article.objects.count(), 3)
        self.assertHttpAccepted(self.api_client.put(self.article_uri_1, format='json', data={
            'title': 'Revised Story',
            'content': "We didn't like the previous version.",
            'authors': [self.author_uri_1],
        }, authentication=self.author_auth_1))
        # Verify no change in count.
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Article.objects.get(pk=self.article_1.pk).title, 'Revised Story')
        self.assertEqual(Article.objects.get(pk=self.article_1.pk).content, "We didn't like the previous version.")

        # But CAN'T update one we don't have authorship of.
        self.assertHttpUnauthorized(self.api_client.put(self.article_uri_2, format='json', data={
            'title': 'Ha, Her Story Was Bad',
            'content': "And she didn't share a bagel with me this morning.",
            'authors': [self.author_uri_1],
        }, authentication=self.author_auth_2))
        # Verify no change in count.
        self.assertEqual(Article.objects.count(), 3)
        # Verify no change in content
        self.assertEqual(Article.objects.get(pk=self.article_2.pk).title, 'Editorial: Why stuff is great')
        self.assertEqual(Article.objects.get(pk=self.article_2.pk).content, 'Because you can buy buy buy & fill the gaping voids in your life.')

    @mock.patch.object(PerUserAuthorization, "update_detail", ret_false)
    def test_put_unauthorized_detail(self):
        resp = self.api_client.put(self.article_uri_1, format='json', data={
            'title': 'Revised Story',
            'content': "We didn't like the previous version.",
            'authors': [self.author_uri_1],
        }, authentication=self.author_auth_1)
        self.assertHttpUnauthorized(resp)

    def test_delete_list(self):
        # Never a delete, not even once.
        self.assertEqual(Article.objects.count(), 3)
        self.assertHttpUnauthorized(self.api_client.delete('/api/v1/article/', format='json', authentication=self.author_auth_1))
        self.assertEqual(Article.objects.count(), 3)

        self.assertHttpUnauthorized(self.api_client.delete('/api/v1/article/', format='json', authentication=self.author_auth_2))
        self.assertEqual(Article.objects.count(), 3)

        self.assertHttpUnauthorized(self.api_client.delete('/api/v1/article/', format='json', authentication=self.author_auth_3))
        self.assertEqual(Article.objects.count(), 3)

    def test_delete_detail(self):
        # Never a delete, not even once.
        self.assertEqual(Article.objects.count(), 3)
        self.assertHttpUnauthorized(self.api_client.delete(self.article_uri_1, format='json', authentication=self.author_auth_1))
        self.assertEqual(Article.objects.count(), 3)

        self.assertHttpUnauthorized(self.api_client.delete(self.article_uri_1, format='json', authentication=self.author_auth_2))
        self.assertEqual(Article.objects.count(), 3)

        self.assertHttpUnauthorized(self.api_client.delete(self.article_uri_1, format='json', authentication=self.author_auth_3))
        self.assertEqual(Article.objects.count(), 3)

    @mock.patch.object(PerUserAuthorization, "delete_detail", ret_false)
    def test_delete_unauthorized_detail(self):
        self.assertEqual(Article.objects.count(), 3)
        self.assertHttpUnauthorized(self.api_client.delete(self.article_uri_1, format='json', authentication=self.author_auth_1))
        self.assertEqual(Article.objects.count(), 3)
