from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from tastypie.test import ResourceTestCase
from .models import AuthorProfile, Article, Shop, Item, Account
from .api.resources import PerUserAuthorization
try:
    import simplejson as json
except ImportError:
    import json
import mock


class PerUserAuthorizationTestCase(ResourceTestCase):
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

    @mock.patch.object(PerUserAuthorization, "read_detail", lambda *args: False)
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

    @mock.patch.object(PerUserAuthorization, "create_detail", lambda *args: False)
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
        the_data = json.loads(resp.content)

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

    @mock.patch.object(PerUserAuthorization, "update_detail", lambda *args: False)
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

    @mock.patch.object(PerUserAuthorization, "delete_detail", lambda *args: False)
    def test_delete_unauthorized_detail(self):
        self.assertEqual(Article.objects.count(), 3)
        self.assertHttpUnauthorized(self.api_client.delete(self.article_uri_1, format='json', authentication=self.author_auth_1))
        self.assertEqual(Article.objects.count(), 3)


class ObjectAuthorizationTestCase(ResourceTestCase):
    def setUp(self):
        super(ObjectAuthorizationTestCase, self).setUp()

        self.user_1 = User.objects.create_user('test_user_1', 'test_user_1@example.com', 'password')
        self.user_2 = User.objects.create_user('test_user_2', 'test_user_2@example.com', 'password')
        self.user_3 = User.objects.create_user('test_user_3', 'test_user_3@example.com', 'password')

        self.account_1 = Account.objects.create(name="Account1", email="acc1@examples.com", user=self.user_1)
        self.account_2 = Account.objects.create(name="Account2", email="acc2@examples.com", user=self.user_2)

        self.shop_1 = Shop.objects.create(owner=self.user_1, name="Shop1")
        self.shop_2 = Shop.objects.create(owner=self.user_2, name="Shop2")
        self.shop_3 = Shop.objects.create(owner=self.user_2, name="Shop3")

        self.item_1 = Item.objects.create(user=self.user_1, name="Item1", shop=self.shop_1)
        self.item_2 = Item.objects.create(user=self.user_1, name="Item2", shop=self.shop_1)
        self.item_3 = Item.objects.create(user=self.user_1, name="Item3", shop=self.shop_1)
        self.item_3.similar.add(self.item_1)
        self.item_3.similar.add(self.item_2)
        self.item_4 = Item.objects.create(user=self.user_2, name="Item4", shop=self.shop_2)

        self.user_auth_1 = self.create_basic('test_user_1', 'password')
        self.user_auth_2 = self.create_basic('test_user_2', 'password')
        self.user_auth_3 = self.create_basic('test_user_3', 'password')

        self.shop_uri_1 = '/api/v1/shop/{0}/'.format(self.shop_1.pk)
        self.shop_uri_2 = '/api/v1/shop/{0}/'.format(self.shop_2.pk)
        self.shop_uri_3 = '/api/v1/shop/{0}/'.format(self.shop_3.pk)
        self.item_uri_1 = '/api/v1/item/{0}/'.format(self.item_1.pk)
        self.item_uri_2 = '/api/v1/item/{0}/'.format(self.item_2.pk)
        self.item_uri_3 = '/api/v1/item/{0}/'.format(self.item_3.pk)
        self.item_uri_4 = '/api/v1/item/{0}/'.format(self.item_4.pk)
        self.user_uri_1 = '/api/v1/user/{0}/'.format(self.user_1.pk)
        self.user_uri_2 = '/api/v1/user/{0}/'.format(self.user_2.pk)
        self.user_uri_3 = '/api/v1/user/{0}/'.format(self.user_3.pk)
        self.userfunc_uri_1 = '/api/v1/userfunc/{0}/'.format(self.user_1.pk)
        self.userfunc_uri_2 = '/api/v1/userfunc/{0}/'.format(self.user_2.pk)
        self.account_uri_1 = '/api/v1/account/{0}/'.format(self.account_1.pk)
        self.account_uri_2 = '/api/v1/account/{0}/'.format(self.account_2.pk)
        self.itemshopowner_uri_1 = '/api/v1/itemshopowner/{0}/'.format(self.item_1.pk)
        self.itemshopowner_uri_2 = '/api/v1/itemshopowner/{0}/'.format(self.item_2.pk)
        self.itemshopowner_uri_3 = '/api/v1/itemshopowner/{0}/'.format(self.item_3.pk)
        self.itemshopowner_uri_4 = '/api/v1/itemshopowner/{0}/'.format(self.item_4.pk)

    def test_obj_get_list(self):
        # User1
        # user's shops
        resp = self.api_client.get('/api/v1/shop/', format='json', authentication=self.user_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        # user's items
        resp = self.api_client.get('/api/v1/item/', format='json', authentication=self.user_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)

        resp = self.api_client.get('/api/v1/itemshopowner/', format='json', authentication=self.user_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)

        resp = self.api_client.get('/api/v1/userfunc/', format='json', authentication=self.user_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        # User2
        # user's shops
        resp = self.api_client.get('/api/v1/shop/', format='json', authentication=self.user_auth_2)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

        # user's items
        resp = self.api_client.get('/api/v1/item/', format='json', authentication=self.user_auth_2)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        resp = self.api_client.get('/api/v1/itemshopowner/', format='json', authentication=self.user_auth_2)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        resp = self.api_client.get('/api/v1/userfunc/', format='json', authentication=self.user_auth_2)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

    def test_obj_get_detail(self):
        # auth
        for pk, shop_uri, user in ((1, self.shop_uri_1, self.user_auth_1),
                                   (2, self.shop_uri_2, self.user_auth_2),
                                   (3, self.shop_uri_3, self.user_auth_2)):
            resp = self.api_client.get(shop_uri, format='json', authentication=user)
            self.assertValidJSONResponse(resp)
            self.assertEqual(self.deserialize(resp)['id'], pk)

        # not auth
        for link, user in ((self.shop_uri_1, self.user_auth_2),
                           (self.shop_uri_2, self.user_auth_1),
                           (self.item_uri_1, self.user_auth_2),
                           (self.item_uri_4, self.user_auth_1),):
            self.assertHttpUnauthorized(self.api_client.get(link, format='json', authentication=user))
            self.assertHttpUnauthorized(self.api_client.get(link, format='json', authentication=user))

        # Account - user1
        resp = self.api_client.get(self.account_uri_1, format='json', authentication=self.user_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)["id"], 1)
        # user 2
        resp = self.api_client.get(self.account_uri_2, format='json', authentication=self.user_auth_2)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)["id"], 2)
        # not auth
        self.assertHttpUnauthorized(self.api_client.get(self.account_uri_1, format='json', authentication=self.user_auth_2))

        # UserFunc
        resp = self.api_client.get(self.userfunc_uri_1, format='json', authentication=self.user_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)["id"], 1)
        # user 2
        resp = self.api_client.get(self.userfunc_uri_2, format='json', authentication=self.user_auth_2)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)["id"], 2)
        # not auth
        self.assertHttpUnauthorized(self.api_client.get(self.userfunc_uri_1, format='json', authentication=self.user_auth_2))

        # Itemshopowner - item1
        resp = self.api_client.get(self.itemshopowner_uri_1, format='json', authentication=self.user_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)["id"], 1)
        # item2
        resp = self.api_client.get(self.itemshopowner_uri_2, format='json', authentication=self.user_auth_1)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)["id"], 2)
        # item4
        resp = self.api_client.get(self.itemshopowner_uri_4, format='json', authentication=self.user_auth_2)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)["id"], 4)
        # not auth
        self.assertHttpUnauthorized(self.api_client.get(self.itemshopowner_uri_1, format='json', authentication=self.user_auth_2))

    def test_obj_post(self):
        # Create shop - auth
        self.assertHttpCreated(self.api_client.post('/api/v1/shop/', format='json', data={
            'name': 'Shop4',
            'owner': self.user_uri_1,
        }, authentication=self.user_auth_1))
        self.assertEqual(Shop.objects.count(), 4)

        # Try create shop - not auth
        self.assertHttpUnauthorized(self.api_client.post('/api/v1/shop/', format='json', data={
            'name': 'Shop5',
            'owner': self.user_uri_2,
        }, authentication=self.user_auth_1))
        self.assertEqual(Shop.objects.count(), 4)

        # Create item
        self.assertHttpCreated(self.api_client.post('/api/v1/item/', format='json', data={
            'name': 'Item5',
            'user': self.user_uri_2,
            'shop': self.shop_uri_2,
        }, authentication=self.user_auth_2))
        self.assertEqual(Item.objects.count(), 5)

        # Try create item - not auth
        self.assertHttpUnauthorized(self.api_client.post('/api/v1/item/', format='json', data={
            'name': 'Item6',
            'user': self.user_uri_1,
            'shop': self.shop_uri_2,
        }, authentication=self.user_auth_2))
        self.assertEqual(Item.objects.count(), 5)

        # Create account
        self.assertHttpCreated(self.api_client.post('/api/v1/account/', format='json', data={
            'name': 'Account3',
            'email': "account3@example.com",
            'user': self.user_uri_3,
        }, authentication=self.user_auth_3))
        self.assertEqual(Account.objects.count(), 3)

        # Create account - not auth
        self.assertHttpUnauthorized(self.api_client.post('/api/v1/account/', format='json', data={
            'name': 'Account3',
            'email': "account3@example.com",
            'user': self.user_uri_3,
        }, authentication=self.user_auth_2))
        self.assertEqual(Account.objects.count(), 3)

    def test_obj_put_and_patch_list(self):
        # items
        resp = self.api_client.get('/api/v1/item/', format='json', authentication=self.user_auth_1)
        self.assertHttpOK(resp)
        data = json.loads(resp.content)
        # change and put
        data['objects'][0]['name'] = 'Item1edit'
        data['objects'][1]['name'] = 'Item2edit'
        data['objects'][2]['name'] = 'Item3edit'
        self.assertHttpAccepted(self.api_client.put('/api/v1/item/', format='json', data=data, authentication=self.user_auth_1))
        self.assertEqual(Item.objects.get(pk=self.item_1.pk).name, 'Item1edit')
        self.assertEqual(Item.objects.get(pk=self.item_2.pk).name, 'Item2edit')
        self.assertEqual(Item.objects.get(pk=self.item_3.pk).name, 'Item3edit')
        # unauthorized this changes for user2
        self.assertHttpUnauthorized(self.api_client.put('/api/v1/item/', format='json', data=data, authentication=self.user_auth_2))

        # shops
        resp = self.api_client.get('/api/v1/shop/', format='json', authentication=self.user_auth_1)
        self.assertHttpOK(resp)
        data = json.loads(resp.content)
        # change and put
        data['objects'][0]['name'] = 'Shop1edit_hihi'
        self.assertHttpAccepted(self.api_client.put('/api/v1/shop/', format='json', data=data, authentication=self.user_auth_1))
        self.assertEqual(Shop.objects.get(pk=self.shop_1.pk).name, 'Shop1edit_hihi')
        # unauthorized this changes for user2
        self.assertHttpUnauthorized(self.api_client.put('/api/v1/shop/', format='json', data=data, authentication=self.user_auth_2))

        # accounts
        resp = self.api_client.get('/api/v1/userfunc/', format='json', authentication=self.user_auth_1)
        self.assertHttpOK(resp)
        data = json.loads(resp.content)
        # change and put
        data['objects'][0]['username'] = 'test_user_1_edit'
        self.assertHttpAccepted(self.api_client.put('/api/v1/userfunc/', format='json', data=data, authentication=self.user_auth_1))
        self.assertEqual(User.objects.get(pk=self.user_1.pk).username, 'test_user_1_edit')
        # unauthorized this changes for user2
        self.assertHttpUnauthorized(self.api_client.put('/api/v1/userfunc/', format='json', data=data, authentication=self.user_auth_2))

        # we changed username, so we have to new auth
        self.user_auth_1 = self.create_basic('test_user_1_edit', 'password')

        resp = self.api_client.get('/api/v1/account/', format='json', authentication=self.user_auth_1)
        self.assertHttpOK(resp)
        data = json.loads(resp.content)
        # change and patch
        data['objects'][0]['name'] = 'Account1edit'
        self.assertHttpAccepted(self.api_client.patch('/api/v1/account/', format='json', data=data, authentication=self.user_auth_1))
        self.assertEqual(Account.objects.get(pk=self.account_1.pk).name, 'Account1edit')
        # unauthorized this changes for user2
        self.assertHttpUnauthorized(self.api_client.patch('/api/v1/account/', format='json', data=data, authentication=self.user_auth_2))

    def test_obj_put_detail(self):
        # Item auth
        self.assertHttpAccepted(self.api_client.put(self.item_uri_1, format='json', data={
            'name': 'Item1edit_obj_put_detail',
            'user': self.user_uri_1,
        }, authentication=self.user_auth_1))
        self.assertEqual(Item.objects.get(pk=self.item_1.pk).name, 'Item1edit_obj_put_detail')

        # Item auth (change in similar)
        self.assertHttpAccepted(self.api_client.put(self.item_uri_3, format='json', data={
            'name': 'Item3edit_obj_put_list',
            'user': self.user_uri_1,
            'similar': [self.item_uri_1, ]
        }, authentication=self.user_auth_1))
        self.assertEqual(Item.objects.get(pk=self.item_3.pk).name, 'Item3edit_obj_put_list')
        self.assertEqual(len(Item.objects.get(pk=self.item_3.pk).similar.all()), 2)

        # Item not auth
        self.assertHttpUnauthorized(self.api_client.put(self.item_uri_1, format='json', data={
            'name': 'Item1edit2_obj_put_detail',
            'user': self.user_uri_1,
        }, authentication=self.user_auth_2))
        self.assertEqual(Item.objects.get(pk=self.item_1.pk).name, 'Item1edit_obj_put_detail')

        # Shop auth
        self.assertHttpAccepted(self.api_client.put(self.shop_uri_1, format='json', data={
            'name': 'Shop1edit_obj_put_detail',
            'owner': self.user_uri_1,
        }, authentication=self.user_auth_1))
        self.assertEqual(Shop.objects.get(pk=self.shop_1.pk).name, 'Shop1edit_obj_put_detail')

        # Shop not auth
        self.assertHttpUnauthorized(self.api_client.put(self.shop_uri_1, format='json', data={
            'name': 'Shop1edit2_obj_put_detail',
            'owner': self.user_uri_1,
        }, authentication=self.user_auth_2))
        self.assertEqual(Shop.objects.get(pk=self.shop_1.pk).name, 'Shop1edit_obj_put_detail')

        # Account auth
        self.assertHttpAccepted(self.api_client.put(self.userfunc_uri_1, format='json', data={
            'username': 'test_user_1_edit',
            'account': self.account_uri_1,
        }, authentication=self.user_auth_1))
        self.assertEqual(User.objects.get(pk=self.user_1.pk).username, 'test_user_1_edit')

        # Account not auth
        self.assertHttpUnauthorized(self.api_client.put(self.userfunc_uri_1, format='json', data={
            'username': 'test_user_1_edit_2',
            'account': self.account_uri_1,
        }, authentication=self.user_auth_2))
        self.assertEqual(User.objects.get(pk=self.user_1.pk).username, 'test_user_1_edit')

        # Shop owner
        resp = self.api_client.get(self.itemshopowner_uri_4, format='json', authentication=self.user_auth_2)
        self.assertHttpOK(resp)
        data = json.loads(resp.content)
        self.assertHttpAccepted(self.api_client.put(self.itemshopowner_uri_4, format='json', data={
            'name': 'Item4edit_shop_owner',
            'user': data['user'],
            'shop': data['shop'],
        }, authentication=self.user_auth_2))
        self.assertEqual(Item.objects.get(pk=self.item_4.pk).name, 'Item4edit_shop_owner')

        # Shop owner not auth; but used PATCH
        self.assertHttpUnauthorized(self.api_client.patch(self.itemshopowner_uri_4, format='json', data={
            'name': 'Item4edit_shop_owner_2',
        }, authentication=self.user_auth_1))
        self.assertEqual(Item.objects.get(pk=self.item_4.pk).name, 'Item4edit_shop_owner')

    def test_obj_delete_list(self):
        # items
        self.assertEqual(Item.objects.count(), 4)
        self.assertHttpAccepted(self.api_client.delete('/api/v1/item/', format='json', authentication=self.user_auth_1))
        self.assertEqual(Item.objects.count(), 1)
        self.assertHttpAccepted(self.api_client.delete('/api/v1/item/', format='json', authentication=self.user_auth_2))
        self.assertEqual(Item.objects.count(), 0)

        # shops
        self.assertEqual(Shop.objects.count(), 3)
        self.assertHttpAccepted(self.api_client.delete('/api/v1/shop/', format='json', authentication=self.user_auth_1))
        self.assertEqual(Shop.objects.count(), 2)
        self.assertHttpAccepted(self.api_client.delete('/api/v1/shop/', format='json', authentication=self.user_auth_2))
        self.assertEqual(Shop.objects.count(), 0)

        # accounts
        self.assertEqual(Account.objects.count(), 2)
        self.assertHttpAccepted(self.api_client.delete('/api/v1/account/', format='json', authentication=self.user_auth_1))
        self.assertEqual(Account.objects.count(), 1)
        self.assertHttpAccepted(self.api_client.delete('/api/v1/account/', format='json', authentication=self.user_auth_2))
        self.assertEqual(Account.objects.count(), 0)

    def test_obj_delete_list_shop__owner(self):
        self.assertEqual(Item.objects.count(), 4)
        self.assertHttpAccepted(self.api_client.delete('/api/v1/itemshopowner/', format='json', authentication=self.user_auth_1))
        self.assertEqual(Item.objects.count(), 1)
        self.assertHttpAccepted(self.api_client.delete('/api/v1/itemshopowner/', format='json', authentication=self.user_auth_2))
        self.assertEqual(Item.objects.count(), 0)

    def test_obj_delete_detail(self):
        # items
        self.assertEqual(Item.objects.count(), 4)
        self.assertHttpAccepted(self.api_client.delete(self.item_uri_1, format='json', authentication=self.user_auth_1))
        self.assertEqual(Item.objects.count(), 3)
        # non auth
        self.assertHttpUnauthorized(self.api_client.delete(self.item_uri_2, format='json', authentication=self.user_auth_2))
        self.assertEqual(Item.objects.count(), 3)

        # shops
        self.assertEqual(Shop.objects.count(), 3)
        self.assertHttpAccepted(self.api_client.delete(self.shop_uri_1, format='json', authentication=self.user_auth_1))
        self.assertEqual(Shop.objects.count(), 2)
        # non auth
        self.assertHttpUnauthorized(self.api_client.delete(self.shop_uri_2, format='json', authentication=self.user_auth_1))
        self.assertEqual(Shop.objects.count(), 2)

        # accounts
        self.assertEqual(Account.objects.count(), 2)
        self.assertHttpAccepted(self.api_client.delete(self.userfunc_uri_1, format='json', authentication=self.user_auth_1))
        self.assertEqual(Account.objects.count(), 1)
        # non auth
        self.assertHttpUnauthorized(self.api_client.delete(self.userfunc_uri_2, format='json', authentication=self.user_auth_1))
        self.assertEqual(Account.objects.count(), 1)

        # delete from account link
        self.assertHttpAccepted(self.api_client.delete(self.account_uri_2, format='json', authentication=self.user_auth_2))
        self.assertEqual(Account.objects.count(), 0)

    def test_obj_delete_detail_shop__owner(self):
        self.assertEqual(Item.objects.count(), 4)
        self.assertHttpAccepted(self.api_client.delete(self.itemshopowner_uri_2, format='json', authentication=self.user_auth_1))
        self.assertEqual(Item.objects.count(), 3)
        # non auth
        self.assertHttpUnauthorized(self.api_client.delete(self.itemshopowner_uri_4, format='json', authentication=self.user_auth_1))
        self.assertEqual(Item.objects.count(), 3)
