from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from core.models import Note, MediaBit
from core.tests.resources import HttpRequest
from core.tests.mocks import MockRequest
from tastypie import fields
from related_resource.api.resources import FreshNoteResource, CategoryResource, PersonResource
from related_resource.api.urls import api
from related_resource.models import Category, Tag, Taggable, TaggableTag, ExtraData, Company, Person, Dog, DogHouse, Bone, Product, Address


class RelatedResourceTest(TestCase):
    urls = 'related_resource.api.urls'

    def setUp(self):
        super(RelatedResourceTest, self).setUp()
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
        request.raw_post_data = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back-2", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00", "author": {"id": %s, "username": "foobar"}}' % self.user.id

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
        request.path = "/v1/tag/%(pk)s/" % {'pk': self.tag_1.pk}
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


class OneToManySetupTestCase(TestCase):
    urls = 'related_resource.api.urls'

    def test_one_to_many(self):
        # Sanity checks.
        self.assertEqual(Note.objects.count(), 2)
        self.assertEqual(MediaBit.objects.count(), 0)

        fnr = FreshNoteResource()

        data = {
            'title': 'Create with related URIs',
            'slug': 'create-with-related-uris',
            'content': 'Some content here',
            'is_active': True,
            'media_bits': [
                {
                    'title': 'Picture #1'
                }
            ]
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = json.dumps(data)

        resp = fnr.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Note.objects.count(), 3)
        note = Note.objects.latest('created')
        self.assertEqual(note.media_bits.count(), 1)
        self.assertEqual(note.media_bits.all()[0].title, u'Picture #1')


class FullCategoryResource(CategoryResource):
    parent = fields.ToOneField('self', 'parent', null=True, full=True)


class RelatedPatchTestCase(TestCase):
    urls = 'related_resource.api.urls'

    def test_patch_to_one(self):
        resource = FullCategoryResource()
        cat1 = Category.objects.create(name='Dad')
        cat2 = Category.objects.create(parent=cat1, name='Child')

        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request.path = "/v1/category/%(pk)s/" % {'pk': cat2.pk}
        request._read_started = False

        data = {
            'name': 'Kid'
        }

        request._raw_post_data = request._body = json.dumps(data)
        self.assertEqual(cat2.name, 'Child')
        resp = resource.patch_detail(request, pk=cat2.pk)
        self.assertEqual(resp.status_code, 202)
        cat2 = Category.objects.get(pk=2)
        self.assertEqual(cat2.name, 'Kid')


class NestedRelatedResourceTest(TestCase):
    urls = 'related_resource.api.urls'

    def test_one_to_one(self):
        """
        Test a related ToOne resource with a nested full ToOne resource
        """
        self.assertEqual(Person.objects.count(), 0)
        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(Address.objects.count(), 0)

        pr = PersonResource()

        data = {
            'name': 'Joan Rivers',
            'company': {
                'name': 'Yum Yum Pie Factory!',
                'address': {
                    'line': 'Somewhere, Utah'
                }
            }
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = json.dumps(data)
        resp = pr.post_list(request)
        self.assertEqual(resp.status_code, 201)

        pk = Person.objects.all()[0].pk
        request = MockRequest()
        request.method = 'GET'
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.get_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 200)

        person = json.loads(resp.content)
        self.assertEqual(person['name'], 'Joan Rivers')

        company = person['company']
        self.assertEqual(company['name'], 'Yum Yum Pie Factory!')

        address = company['address']
        self.assertEqual(address['line'], 'Somewhere, Utah')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        request.raw_post_data = resp.content
        resp = pr.put_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 204)

    def test_one_to_many(self):
        """
        Test a related ToOne resource with a nested full ToMany resource
        """
        self.assertEqual(Person.objects.count(), 0)
        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)

        pr = PersonResource()

        data = {
            'name': 'Joan Rivers',
            'company': {
                'name': 'Yum Yum Pie Factory!',
                'products': [
                    {
                        'name': 'Tasty Pie'
                    }
                ]
            }
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = json.dumps(data)
        resp = pr.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Product.objects.count(), 1)

        pk = Person.objects.all()[0].pk
        request = MockRequest()
        request.method = 'GET'
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.get_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 200)

        person = json.loads(resp.content)
        self.assertEqual(person['name'], 'Joan Rivers')

        company = person['company']
        self.assertEqual(company['name'], 'Yum Yum Pie Factory!')
        self.assertEqual(len(company['products']), 1)

        product = company['products'][0]
        self.assertEqual(product['name'], 'Tasty Pie')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        request.raw_post_data = json.dumps(person)
        resp = pr.put_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 204)

    def test_many_to_one(self):
        """
        Test a related ToMany resource with a nested full ToOne resource
        """
        self.assertEqual(Person.objects.count(), 0)
        self.assertEqual(Dog.objects.count(), 0)
        self.assertEqual(DogHouse.objects.count(), 0)

        pr = PersonResource()

        data = {
            'name': 'Joan Rivers',
            'dogs': [
                {
                    'name': 'Snoopy',
                    'house': {
                        'color': 'Red'
                    }
                }
            ]
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.raw_post_data = json.dumps(data)
        resp = pr.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Dog.objects.count(), 1)
        self.assertEqual(DogHouse.objects.count(), 1)

        pk = Person.objects.all()[0].pk
        request = MockRequest()
        request.method = 'GET'
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.get_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 200)

        person = json.loads(resp.content)
        self.assertEqual(person['name'], 'Joan Rivers')
        self.assertEqual(len(person['dogs']), 1)

        dog = person['dogs'][0]
        self.assertEqual(dog['name'], 'Snoopy')

        house = dog['house']
        self.assertEqual(house['color'], 'Red')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.raw_post_data = json.dumps(person)
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.put_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 204)

    def test_many_to_many(self):
        """
        Test a related ToMany resource with a nested full ToMany resource
        """
        self.assertEqual(Person.objects.count(), 0)
        self.assertEqual(Dog.objects.count(), 0)
        self.assertEqual(Bone.objects.count(), 0)

        pr = PersonResource()

        data = {
            'name': 'Joan Rivers',
            'dogs': [
                {
                    'name': 'Snoopy',
                    'bones': [
                        {
                            'color': 'white'
                        }
                    ]
                }
            ]
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.path = reverse('api_dispatch_list', kwargs={'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        request.raw_post_data = json.dumps(data)
        resp = pr.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Dog.objects.count(), 1)
        self.assertEqual(Bone.objects.count(), 1)

        pk = Person.objects.all()[0].pk
        request = MockRequest()
        request.method = 'GET'
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.get_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 200)

        person = json.loads(resp.content)
        self.assertEqual(person['name'], 'Joan Rivers')
        self.assertEqual(len(person['dogs']), 1)

        dog = person['dogs'][0]
        self.assertEqual(dog['name'], 'Snoopy')
        self.assertEqual(len(dog['bones']), 1)

        bone = dog['bones'][0]
        self.assertEqual(bone['color'], 'white')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.raw_post_data = json.dumps(person)
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.put_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 204)
