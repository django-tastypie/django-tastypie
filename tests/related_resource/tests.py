import json
from django.contrib.auth.models import User
from django.test import TestCase
from core.tests.mocks import MockRequest
from django.conf import settings
from related_resource.api.resources import UserResource, \
        CategoryResource, TagResource, TaggableResource, TaggableTagResource, \
        ExtraDataResource, GenericTagResource
from related_resource.api.urls import api
from related_resource.models import Category, Tag, Taggable, TaggableTag, ExtraData, GenericTag
from django.contrib.contenttypes.models import ContentType
from tastypie.resources import ContentTypeResource

settings.DEBUG = True

class RelatedResourceTest(TestCase):
    urls = 'related_resource.api.urls'

    def setUp(self):
        self.user = User.objects.create(username="testy_mctesterson")

    def test_cannot_access_user_resource(self):
        resource = api.canonical_resource_for('users')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.raw_post_data = '{"username": "foobar"}'
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.user.pk)

        self.assertEqual(resp.status_code, 405)
        self.assertEqual(User.objects.get(id=self.user.id).username, self.user.username)

    def test_related_resource_authorization(self):
        resource = api.canonical_resource_for('notes')
        
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00", "author": null}'
        
        resp = resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(User.objects.get(id=self.user.id).username, 'testy_mctesterson')
        
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00", "author": {"id": %s, "username": "foobar"}}' % self.user.id
        
        resp = resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(User.objects.get(id=self.user.id).username, 'foobar')


class CategoryResourceTest(TestCase):
    urls = 'related_resource.api.urls'

    def setUp(self):
        super(CategoryResourceTest, self).setUp()
        self.parent_cat_1 = Category.objects.create(parent=None, name='Dad')
        self.parent_cat_2 = Category.objects.create(parent=None, name='Mom')
        self.child_cat_1 = Category.objects.create(parent=self.parent_cat_1, name='Son')
        self.child_cat_2 = Category.objects.create(parent=self.parent_cat_2, name='Daughter')

    def test_correct_relation(self):
        resource = api.canonical_resource_for('category')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.parent_cat_1.pk)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['parent'], None)
        self.assertEqual(data['name'], 'Dad')

        # Now try a child.
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.child_cat_2.pk)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['parent'], '/v1/category/2/')
        self.assertEqual(data['name'], 'Daughter')

    def test_put_null(self):
        resource = api.canonical_resource_for('category')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.raw_post_data = '{"parent": null, "name": "Son"}'

        # Before the PUT, there should be a parent.
        self.assertEqual(Category.objects.get(pk=self.child_cat_1.pk).parent.pk, self.parent_cat_1.pk)

        # After the PUT, the parent should be ``None``.
        resp = resource.put_detail(request, pk=self.child_cat_1.pk)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Category.objects.get(pk=self.child_cat_1.pk).name, 'Son')
        self.assertEqual(Category.objects.get(pk=self.child_cat_1.pk).parent, None)


class ExplicitM2MResourceRegressionTest(TestCase):
    urls = 'related_resource.api.urls'

    def setUp(self):
        super(ExplicitM2MResourceRegressionTest, self).setUp()
        self.tag_1 = Tag.objects.create(name='important')
        self.taggable_1 = Taggable.objects.create(name='exam')

        # Create relations between tags and taggables through the explicit m2m table
        self.taggabletag_1 = TaggableTag.objects.create(tag=self.tag_1, taggable=self.taggable_1)

        # Give each tag some extra data (the lookup of this data is what makes the test fail)
        self.extradata_1 = ExtraData.objects.create(tag=self.tag_1, name='additional')


    def test_correct_setup(self):
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        # Verify the explicit 'through' relationships has been created correctly
        resource = api.canonical_resource_for('taggabletag')
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.taggabletag_1.pk)
        data = json.loads(resp.content)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['tag'], '/v1/tag/1/')
        self.assertEqual(data['taggable'], '/v1/taggable/1/')

        resource = api.canonical_resource_for('taggable')
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.taggable_1.pk)
        data = json.loads(resp.content)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['name'], 'exam')

        resource = api.canonical_resource_for('tag')
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.tag_1.pk)
        data = json.loads(resp.content)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['name'], 'important')

        # and check whether the extradata is present
        self.assertEqual(data['extradata']['name'], u'additional')


    def test_post_new_tag(self):
        resource = api.canonical_resource_for('tag')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = '{"name": "school", "taggabletags": [ ]}'

        # Prior to the addition of ``blank=True``, this would
        # fail badly.
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 201)

        # GET the created object (through its headers.location)
        self.assertTrue(resp.has_header('location'))
        location = resp['Location']

        resp = self.client.get(location, data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content)
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], 'school')

class GenericForeignKeyTest(TestCase):
    urls = 'related_resource.api.urls'
    
    def setUp(self):
        super(GenericForeignKeyTest, self).setUp()
        # create some test objects to point generic relations to
        self.category_1 = Category.objects.create(name="Programming")
        self.taggable_1 = Taggable.objects.create(name="Programming Post")
        # create a tag resources
        self.tag_1 = GenericTag.objects.create(name='Python', 
                                content_object=self.category_1)
        self.tag_2 = GenericTag.objects.create(name='Django',
                                content_object=self.taggable_1)
    
    def test_read_tag_content_object(self):

        # access tag_1 through the database and assert that the content_object
        # points to category_1
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resource = api.canonical_resource_for('generictag')
        # should get us self.tag_1
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.tag_1.pk)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        # test that the uri for content_object pointed to self.category_1
        self.assertEqual(data['content_object'], 
                        CategoryResource().get_resource_uri(self.category_1))
        
        # should get us self.tag_2
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.tag_2.pk)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['content_object'], 
                    TaggableResource().get_resource_uri(self.taggable_1))
    
    def test_read_tag_content_object_full(self):
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        # set the content_object field to full mode
        resource = api.canonical_resource_for('generictag')
        resource.fields['content_object'].full = True
        
        # check for self.tag_1 and self.category_1
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.tag_1.pk)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['content_object'], 
            CategoryResource().full_dehydrate(
                    CategoryResource().build_bundle(obj=self.category_1, 
                        request=request)).data)
        
        # now for self.tag_2 and self.taggable_1
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.tag_2.pk)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['content_object'], 
            TaggableResource().full_dehydrate(
                    TaggableResource().build_bundle(obj=self.taggable_1, 
                        request=request)).data)
    
    def test_post_by_uri(self):
        """Create a new GenericTag item using POST request. 
        Point content_object to a category by it's uri"""
        new_category = Category.objects.create(name="Design")
        self.assertEqual(new_category.name, "Design")
        
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = '{"name": "Photoshop", "content_object": "%s"}' % CategoryResource().get_resource_uri(new_category)
        
        resource = api.canonical_resource_for('generictag')
        
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 201)
        
        # get newly created object via headers.locaion
        self.assertTrue(resp.has_header('location'))
        location = resp['location']
        
        resp = self.client.get(location, data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['name'], 'Photoshop')
        self.assertEqual(data['content_object'], 
                CategoryResource().get_resource_uri(new_category))
        
        # now try doing this with a TaggableObject instead
        
        new_taggable = Taggable.objects.create(name="Design Post")
        
        request.raw_post_data = '{"name": "UX", "content_object": "%s"}' % TaggableResource().get_resource_uri(new_taggable)
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 201)
        
        self.assertTrue(resp.has_header('location'))
        location = resp['location']
        
        resp = self.client.get(location, data={"format" : "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['name'], 'UX')
        self.assertEqual(data['content_object'],
            TaggableResource().get_resource_uri(new_taggable))
    
    def test_post_by_data_requires_content_type(self):
        """Make sure 400 (BadRequest) is the response if an attempt is made to post with data
        for the GenericForeignKey without providing a content_type
        """
        
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = '{"name": "Photoshop", "content_object": %s}' % '{"name": "Design"}'
        
        resource = api.canonical_resource_for('generictag')
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertTrue(resp.status_code, 400)
        
    def test_post_by_data(self):
        """Create a new GenericTag item using a POST request.
        content_type must be set on the new object and the serialized 
        data for the GenericForeignKey will be included in the POST 
        """
        
        new_category = Category(name="Design")
        self.assertEqual(new_category.name, "Design")
        
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = (
            '{"name": "Photoshop", "content_type": "%s", "content_object": {"name": "Design"}}' 
                % (ContentTypeResource().get_resource_uri(
                        ContentType.objects.get_for_model(Category))))
        
        resource = api.canonical_resource_for('generictag')
        
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 201)
        
        # get newly created object via headers.locaion
        self.assertTrue(resp.has_header('location'))
        location = resp['location']
        
        resp = self.client.get(location, data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['name'], 'Photoshop')
        self.assertTrue(data['content_object'])
        resp = self.client.get(data['content_object'], data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['name'], new_category.name)
        # make sure this represents a category
        self.assertEqual(type(resource.get_via_uri(data['resource_uri'])), 
                         Category)
        
        # test posting taggable data instead of category this time
        request.raw_post_data = (
            '{"name": "Photoshop", "content_type": "%s", "content_object": {"name": "Design Post"}}' 
                % (ContentTypeResource().get_resource_uri(
                        ContentType.objects.get_for_model(Taggable))))
        
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 201)
        
        # get newly created object via headers.locaion
        self.assertTrue(resp.has_header('location'))
        location = resp['location']
        
        resp = self.client.get(location, data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['name'], 'Photoshop')
        self.assertTrue(data['content_object'])
        resp = self.client.get(data['content_object'], data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['name'], "Design Post")
        # make sure this represents a category
        self.assertEqual(type(resource.get_via_uri(data['resource_uri'])), 
                         Taggable)
                         
    def test_put(self):
        new_category = Category.objects.create(name="Design")
        self.assertEqual(new_category.name, "Design")
        
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = '{"name": "Photoshop", "content_object": "%s"}' % CategoryResource().get_resource_uri(new_category)
        
        resource = api.canonical_resource_for('generictag')
        
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 201)

        # get newly created object via headers.locaion
        self.assertTrue(resp.has_header('location'))
        location = resp['location']
        
        # put to this location and replace the name of content_object with "Web Design"
        resp = self.client.get(location, data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['name'], 'Photoshop')
        self.assertEqual(data['content_object'], 
                CategoryResource().get_resource_uri(new_category))
        # now put the new data
        request.raw_post_data = '{"content_object": {"name": "Web Design"}}'
        request.method = 'PUT'
        resp = resource.put_detail(request, pk=data['id'])
        self.assertEqual(resp.status_code, 204)
        
        # test putting a different content type
        request.raw_post_data = ('{"content_type": "%s", "content_object": {"name": "Web Design"}}' 
            % (ContentTypeResource().get_resource_uri(
                    ContentType.objects.get_for_model(Taggable))))
        resp = resource.put_detail(request, pk=data['id'])
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(GenericTag.objects.get(pk=data['id']).content_type, ContentType.objects.get_for_model(Taggable))
    
    def test_reverse(self):
        tags = self.category_1.tags.all()
        
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        
        resource = api.canonical_resource_for('generictag')
        resource.fields['content_object'].full = False
        # should get us self.tag_1
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.tag_1.pk)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        # test that the uri for content_object pointed to self.category_1
        self.assertEqual(data['content_object'], 
                        CategoryResource().get_resource_uri(self.category_1))
        
        resp = self.client.get(data['content_object'], data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        tags_urls = list()
        for tag in tags:
            tags_urls.append(GenericTagResource().get_resource_uri(tag))
        self.assertEqual(data['tags'], tags_urls)
        
        # add some more tags to this category
        GenericTag.objects.create(name="Object Orientated", content_object=self.category_1)
        GenericTag.objects.create(name="Interpreted", content_object=self.category_1)
        
        tags = self.category_1.tags.all()
        tags_urls = list()
        for tag in tags:
            tags_urls.append(GenericTagResource().get_resource_uri(tag))
        
        resp = self.client.get(data['resource_uri'], data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['tags'], tags_urls)