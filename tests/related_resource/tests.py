from datetime import datetime
import json

import django
from django.contrib.auth.models import User
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save
from django.test.testcases import TestCase
from django.test.utils import override_settings

from tastypie import fields
from tastypie.exceptions import ApiFieldError, NotFound

from core.models import Note, MediaBit
from core.tests.mocks import MockRequest

from related_resource.api.resources import AddressResource, CategoryResource,\
    ForumResource, FreshNoteResource, JobResource, NoteResource,\
    OrderResource, NoteWithUpdatableUserResource, PersonResource, TagResource,\
    UserResource
from related_resource.api.urls import api
from related_resource.models import Category, Label, Tag, Taggable,\
    TaggableTag, ExtraData, Company, Person, Dog, DogHouse, Bone, Product,\
    Address, Job, Payment, Forum, Order, OrderItem, Contact, ContactGroup
from testcases import TestCaseWithFixture


class M2MResourcesTestCase(TestCaseWithFixture):
    def test_same_object_added(self):
        """
        From Issue #1035
        """
        user = User.objects.create(username='gjcourt')

        ur = UserResource()
        fr = ForumResource()

        resp = self.client.post(fr.get_resource_uri(), content_type='application/json', data=json.dumps({
            'name': 'Test Forum',
            'members': [ur.get_resource_uri(user)],
            'moderators': [ur.get_resource_uri(user)],
        }))

        self.assertEqual(resp.status_code, 201, resp.content)

        data = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(len(data['moderators']), 1)
        self.assertEqual(len(data['members']), 1)


@override_settings(ROOT_URLCONF='related_resource.api.urls')
class RelatedResourceTest(TestCaseWithFixture):
    def setUp(self):
        super(RelatedResourceTest, self).setUp()
        self.user = User.objects.create(username="testy_mctesterson")

    def test_cannot_access_user_resource(self):
        resource = api.canonical_resource_for('users')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"username": "foobar"}')
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.user.pk)

        self.assertEqual(resp.status_code, 405)
        self.assertEqual(User.objects.get(id=self.user.id).username, self.user.username)

    def test_related_resource_authorization(self):
        resource = api.canonical_resource_for('notes')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00", "author": null}')

        resp = resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(User.objects.get(id=self.user.id).username, 'testy_mctesterson')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back-2", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00", "author": {"id": %s, "username": "foobar"}}' % self.user.id)

        resp = resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(User.objects.get(id=self.user.id).username, 'foobar')

    def test_ok_not_null_field_included(self):
        """
        Posting a new detail with no related objects
        should require one query to save the object
        """
        company = Company.objects.create()

        resource = api.canonical_resource_for('product')

        request = MockRequest()
        body = json.dumps({
            'producer': {'pk': company.pk},
        })
        request.set_body(body)

        resp = resource.post_list(request)

        self.assertEqual(resp.status_code, 201)

    def test_apifielderror_missing_not_null_field(self):
        """
        Posting a new detail with no related objects
        should require one query to save the object
        """
        resource = api.canonical_resource_for('product')

        request = MockRequest()
        body = json.dumps({})
        request.set_body(body)

        with self.assertRaises(ApiFieldError):
            resource.post_list(request)


@override_settings(ROOT_URLCONF='related_resource.api.urls')
class CategoryResourceTest(TestCaseWithFixture):
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
        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(data['parent'], None)
        self.assertEqual(data['name'], 'Dad')

        # Now try a child.
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.child_cat_2.pk)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(data['parent'], '/v1/category/2/')
        self.assertEqual(data['name'], 'Daughter')

    def test_put_null(self):
        resource = api.canonical_resource_for('category')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"parent": null, "name": "Son"}')

        # Before the PUT, there should be a parent.
        self.assertEqual(Category.objects.get(pk=self.child_cat_1.pk).parent.pk, self.parent_cat_1.pk)

        # After the PUT, the parent should be ``None``.
        resp = resource.put_detail(request, pk=self.child_cat_1.pk)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Category.objects.get(pk=self.child_cat_1.pk).name, 'Son')
        self.assertEqual(Category.objects.get(pk=self.child_cat_1.pk).parent, None)


@override_settings(ROOT_URLCONF='related_resource.api.urls')
class ExplicitM2MResourceRegressionTest(TestCaseWithFixture):
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
        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['tag'], '/v1/tag/1/')
        self.assertEqual(data['taggable'], '/v1/taggable/1/')

        resource = api.canonical_resource_for('taggable')
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.taggable_1.pk)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['name'], 'exam')

        resource = api.canonical_resource_for('tag')
        request.path = "/v1/tag/%(pk)s/" % {'pk': self.tag_1.pk}
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.tag_1.pk)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['name'], 'important')

        # and check whether the extradata is present
        self.assertEqual(data['extradata']['name'], u'additional')

    def test_post_new_tag(self):
        resource = api.canonical_resource_for('tag')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.set_body('{"name": "school", "taggabletags": [ ]}')

        # Prior to the addition of ``blank=True``, this would
        # fail badly.
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 201)

        # GET the created object (through its headers.location)
        self.assertTrue(resp.has_header('location'))
        location = resp['Location']

        resp = self.client.get(location, data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)
        deserialized = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(deserialized), 5)
        self.assertEqual(deserialized['name'], 'school')


@override_settings(ROOT_URLCONF='related_resource.api.urls')
class OneToManySetupTestCase(TestCaseWithFixture):
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
        request.set_body(json.dumps(data))

        resp = fnr.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Note.objects.count(), 3)
        note = Note.objects.latest('created')
        self.assertEqual(note.media_bits.count(), 1)
        self.assertEqual(note.media_bits.all()[0].title, u'Picture #1')


class FullCategoryResource(CategoryResource):
    parent = fields.ToOneField('self', 'parent', null=True, full=True)


class RelationshipOppositeFromModelTestCase(TestCaseWithFixture):
    """
        On the model, the Job relationship is defined on the Payment.
        On the resource, the PaymentResource is defined on the JobResource as well
    """
    def setUp(self):
        super(RelationshipOppositeFromModelTestCase, self).setUp()

        # a job with a payment exists to start with
        self.some_time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        job = Job.objects.create(name='SomeJob')
        Payment.objects.create(job=job, scheduled=self.some_time_str)

    def test_create_similar(self):
        # We submit to job with the related payment included.
        # Note that on the resource, the payment related resource is defined
        # On the model, the Job class does not have a payment field,
        # but it has a reverse relationship defined by the Payment class
        resource = JobResource()
        data = {
            'name': 'OtherJob',
            'payment': {
                'scheduled': self.some_time_str
            }
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.set_body(json.dumps(data))

        resp = resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Job.objects.count(), 2)
        self.assertEqual(Payment.objects.count(), 2)

        new_job = Job.objects.all().order_by('-id')[0]
        new_payment = Payment.objects.all().order_by('-id')[0]

        self.assertEqual(new_job.name, 'OtherJob')
        self.assertEqual(new_job, new_payment.job)


@override_settings(ROOT_URLCONF='related_resource.api.urls')
class RelatedPatchTestCase(TestCaseWithFixture):
    def test_patch_to_one(self):
        resource = FullCategoryResource()
        cat1 = Category.objects.create(name='Dad')
        cat2 = Category.objects.create(parent=cat1, name='Child')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request.path = "/v1/category/%(pk)s/" % {'pk': cat2.pk}

        data = {
            'name': 'Kid'
        }

        request.set_body(json.dumps(data))

        self.assertEqual(cat2.name, 'Child')

        resp = resource.patch_detail(request, pk=cat2.pk)

        self.assertEqual(resp.status_code, 202)

        cat2 = Category.objects.get(pk=2)

        self.assertEqual(cat2.name, 'Kid')

    def test_patch_detail_with_missing_related_fields(self):
        """
        When fields are excluded the value of the field should not be set to a
        default value if updated by tastypie.
        """
        resource = NoteWithUpdatableUserResource()
        note = Note.objects.create(author_id=1)
        user = User.objects.get(pk=1)

        self.assertEqual(user.password, 'this_is_not_a_valid_password_string')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request.path = "/v1/noteswithupdatableuser/%(pk)s/" % {'pk': note.pk}

        data = {
            'author': {
                'id': 1,
                'username': 'johndoe',
                'email': 'john@doetown.com',
            }
        }

        request.set_body(json.dumps(data))

        resp = resource.patch_detail(request, pk=note.pk)

        self.assertEqual(resp.status_code, 202)

        user2 = User.objects.get(pk=1)

        self.assertEqual(user2.email, 'john@doetown.com')
        self.assertEqual(user2.password, 'this_is_not_a_valid_password_string')

    def test_patch_detail_dont_update_related_without_permission(self):
        """
        When fields are excluded the value of the field should not be set to a
        default value if updated by tastypie.
        """
        resource = NoteResource()
        note = Note.objects.create(author_id=1)
        user = User.objects.get(pk=1)

        self.assertEqual(user.password, 'this_is_not_a_valid_password_string')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request.path = "/v1/note/%(pk)s/" % {'pk': note.pk}

        data = {
            'author': {
                'id': 1,
                'username': 'johndoe',
                'email': 'john@doetown.com',
            }
        }

        request.set_body(json.dumps(data))

        resp = resource.patch_detail(request, pk=note.pk)

        self.assertEqual(resp.status_code, 202)

        user2 = User.objects.get(pk=1)

        self.assertEqual(user2.email, 'john@doetown.com')
        self.assertEqual(user2.password, 'this_is_not_a_valid_password_string')


@override_settings(ROOT_URLCONF='related_resource.api.urls')
class NestedRelatedResourceTest(TestCaseWithFixture):
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
        request.set_body(json.dumps(data))
        resp = pr.post_list(request)
        self.assertEqual(resp.status_code, 201)

        pk = Person.objects.all()[0].pk
        request = MockRequest()
        request.method = 'GET'
        request.path = reverse('api_dispatch_detail', kwargs={
            'pk': pk,
            'resource_name': pr._meta.resource_name,
            'api_name': pr._meta.api_name
        })
        resp = pr.get_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 200)

        person = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(person['name'], 'Joan Rivers')

        company = person['company']
        self.assertEqual(company['name'], 'Yum Yum Pie Factory!')

        address = company['address']
        self.assertEqual(address['line'], 'Somewhere, Utah')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.path = reverse('api_dispatch_detail', kwargs={
            'pk': pk,
            'resource_name': pr._meta.resource_name,
            'api_name': pr._meta.api_name
        })
        request.set_body(resp.content.decode('utf-8'))
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
        request.set_body(json.dumps(data))
        resp = pr.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Product.objects.count(), 1)

        pk = Person.objects.all()[0].pk
        request = MockRequest()
        request.method = 'GET'
        resp = pr.get_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 200)

        person = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(person['name'], 'Joan Rivers')

        company = person['company']
        self.assertEqual(company['name'], 'Yum Yum Pie Factory!')
        self.assertEqual(len(company['products']), 1)

        product = company['products'][0]
        self.assertEqual(product['name'], 'Tasty Pie')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body(json.dumps(person))
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
        request.set_body(json.dumps(data))
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

        person = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(person['name'], 'Joan Rivers')
        self.assertEqual(len(person['dogs']), 1)

        dog = person['dogs'][0]
        self.assertEqual(dog['name'], 'Snoopy')

        house = dog['house']
        self.assertEqual(house['color'], 'Red')

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body(json.dumps(person))
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.put_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 204)

    def test_many_to_one_extra_data_ignored(self):
        """
        Test a related ToMany resource with a nested full ToOne resource

        FieldError would result when extra data is included on an embedded
        resource for an already saved object.
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
        request.set_body(json.dumps(data))
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

        person = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(person['name'], 'Joan Rivers')
        self.assertEqual(len(person['dogs']), 1)

        dog = person['dogs'][0]
        self.assertEqual(dog['name'], 'Snoopy')

        house = dog['house']
        self.assertEqual(house['color'], 'Red')

        # clients may include extra data, which should be ignored. Make extra data is ignored on the resource and sub resources.
        person['thisfieldshouldbeignored'] = 'foobar'
        person['dogs'][0]['thisfieldshouldbeignored'] = 'foobar'

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body(json.dumps(person))
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
        request.set_body(json.dumps(data))
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

        person = json.loads(resp.content.decode('utf-8'))
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
        request.set_body(json.dumps(person))
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.put_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 204)

    def test_many_to_many_change_nested(self):
        """
        Test a related ToMany resource with a nested full ToMany resource
        """
        self.assertEqual(Person.objects.count(), 0)
        self.assertEqual(Dog.objects.count(), 0)
        self.assertEqual(Bone.objects.count(), 0)

        pr = PersonResource()

        person = Person.objects.create(name='Joan Rivers')
        dog = person.dogs.create(name='Snoopy')
        bone = dog.bones.create(color='white')

        pk = person.pk
        request = MockRequest()
        request.method = 'GET'
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.get_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(data['dogs'][0]['bones'][0]['color'], 'white')

        # Change just a nested resource via PUT
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        data['dogs'][0]['bones'][0]['color'] = 'gray'
        body = json.dumps(data)
        request.set_body(body)
        request.path = reverse('api_dispatch_detail', kwargs={'pk': pk, 'resource_name': pr._meta.resource_name, 'api_name': pr._meta.api_name})
        resp = pr.put_detail(request, pk=pk)
        self.assertEqual(resp.status_code, 204)

        self.assertEqual(Bone.objects.count(), 1)
        bone = Bone.objects.all()[0]
        self.assertEqual(bone.color, 'gray')


@override_settings(ROOT_URLCONF='related_resource.api.urls')
class RelatedSaveCallsTest(TestCaseWithFixture):
    def test_one_query_for_post_list(self):
        """
        Posting a new detail with no related objects
        should require one query to save the object
        """
        resource = api.canonical_resource_for('category')

        request = MockRequest()
        body = json.dumps({
            'name': 'Foo',
            'parent': None
        })
        request.set_body(body)

        with self.assertNumQueries(1):
            resource.post_list(request)

    def test_two_queries_for_post_list(self):
        """
        Posting a new detail with one related object, referenced via its
        ``resource_uri`` should require two queries: one to save the
        object, and one to lookup the related object.
        """
        parent = Category.objects.create(name='Bar')
        resource = api.canonical_resource_for('category')

        request = MockRequest()
        body = json.dumps({
            'name': 'Foo',
            'parent': resource.get_resource_uri(parent)
        })

        request.set_body(body)

        with self.assertNumQueries(2):
            resource.post_list(request)

    def test_no_save_m2m_unchanged(self):
        """
        Posting a new detail with a related m2m object shouldn't
        save the m2m object unless the m2m object is provided inline.
        """
        def _save_fails_test(sender, **kwargs):
            self.fail("Should not have saved Label")

        pre_save.connect(_save_fails_test, sender=Label)
        l1 = Label.objects.get(name='coffee')
        resource = api.canonical_resource_for('post')
        label_resource = api.canonical_resource_for('label')

        request = MockRequest()

        body = json.dumps({
            'name': 'test post',
            'label': [label_resource.get_resource_uri(l1)],
        })

        request.set_body(body)

        resource.post_list(request)  # _save_fails_test will explode if Label is saved

    def test_save_m2m_changed(self):
        """
        Posting a new or updated detail object with a related m2m object
        should save the m2m object if it's included inline.
        """
        resource = api.canonical_resource_for('tag')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        body_dict = {
            'name': 'school',
            'taggabletags': [{'extra': 7}]
        }

        request.set_body(json.dumps(body_dict))

        with self.assertNumQueries(4):
            resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 201)

        # 'extra' should have been set
        tag = Tag.objects.all()[0]
        taggable_tag = tag.taggabletags.all()[0]
        self.assertEqual(taggable_tag.extra, 7)

        body_dict['taggabletags'] = [{'extra': 1234}]

        request.set_body(json.dumps(body_dict))

        request.path = reverse('api_dispatch_detail', kwargs={
            'pk': tag.pk,
            'resource_name': resource._meta.resource_name,
            'api_name': resource._meta.api_name
        })

        with self.assertNumQueries(5):
            resource.put_detail(request)

        # 'extra' should have changed
        tag = Tag.objects.all()[0]
        taggable_tag = tag.taggabletags.all()[0]
        self.assertEqual(taggable_tag.extra, 1234)

    def test_no_save_m2m_unchanged_existing_data_persists(self):
        """
        Data should persist when posting an updated detail object with
        unchanged reverse related objects.
        """
        person = Person.objects.create(name='Ryan')
        dog = Dog.objects.create(name='Wilfred', owner=person)
        bone1 = Bone.objects.create(color='White', dog=dog)
        bone2 = Bone.objects.create(color='Grey', dog=dog)

        self.assertEqual(dog.bones.count(), 2)

        resource = api.canonical_resource_for('dog')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request._load_post_and_files = lambda *args, **kwargs: None
        body_dict = {
            'id': dog.id,
            'name': 'Wilfred',
            'bones': [
                {'id': bone1.id, 'color': bone1.color},
                {'id': bone2.id, 'color': bone2.color}
            ]
        }

        request.set_body(json.dumps(body_dict))

        with self.assertNumQueries(13 if django.VERSION >= (1, 9) else 14):
            resp = resource.wrap_view('dispatch_detail')(request, pk=dog.pk)

        self.assertEqual(resp.status_code, 204)

        dog = Dog.objects.all()[0]

        dog_bones = dog.bones.all()

        self.assertEqual(len(dog_bones), 2)

        self.assertEqual(dog_bones[0], bone1)
        self.assertEqual(dog_bones[1], bone2)

    def test_no_save_m2m_related(self):
        """
        When saving an object with a M2M field, don't save that related object's related objects.
        """
        cg1 = ContactGroup.objects.create(name='The Inebriati')
        cg2 = ContactGroup.objects.create(name='The Stone Cutters')

        c1 = Contact.objects.create(name='foo')
        c2 = Contact.objects.create(name='bar')
        c2.groups.add(cg1, cg2)
        c3 = Contact.objects.create(name='baz')
        c3.groups.add(cg1)

        self.assertEqual(list(c1.groups.all()), [])
        self.assertEqual(list(c2.groups.all()), [cg1, cg2])
        self.assertEqual(list(c3.groups.all()), [cg1])

        data = {
            'name': c1.name,
            'groups': [reverse('api_dispatch_detail', kwargs={'api_name': 'v1', 'resource_name': 'contactgroup', 'pk': cg1.pk})],
        }

        resource = api.canonical_resource_for('contact')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request._load_post_and_files = lambda *args, **kwargs: None
        request.set_body(json.dumps(data))

        with self.withAssertNumQueriesLessThan(9):
            response = resource.wrap_view('dispatch_detail')(request, pk=c1.pk)

        self.assertEqual(response.status_code, 204, response.content)

        new_contacts = Contact.objects.all()
        new_c1 = new_contacts[0]
        new_c2 = new_contacts[1]
        new_c3 = new_contacts[2]

        self.assertEqual(new_c1.name, c1.name)

        self.assertEqual(new_c1.id, c1.id)
        self.assertEqual(list(new_c1.groups.all()), [cg1])
        self.assertEqual(new_c2.id, c2.id)
        self.assertEqual(list(new_c2.groups.all()), [cg1, cg2])
        self.assertEqual(new_c3.id, c3.id)
        self.assertEqual(list(new_c3.groups.all()), [cg1])

        new_cg1 = ContactGroup.objects.get(id=cg1.id)
        new_cg2 = ContactGroup.objects.get(id=cg2.id)

        self.assertEqual(list(new_cg1.members.all()), [new_c1, new_c2, new_c3])
        self.assertEqual(list(new_cg2.members.all()), [new_c2])


@override_settings(ROOT_URLCONF='related_resource.api.urls')
class CorrectUriRelationsTestCase(TestCaseWithFixture):
    """
    Validate that incorrect URI (with PKs that line up to valid data) are not
    accepted.
    """
    def test_incorrect_uri(self):
        self.assertEqual(Note.objects.count(), 2)
        nr = NoteResource()

        # For this test, we need a ``User`` with the same PK as a ``Note``.
        note_1 = Note.objects.latest('created')
        User.objects.create(
            id=note_1.pk,
            username='valid',
            email='valid@exmaple.com',
            password='junk'
        )

        data = {
            # This URI is flat-out wrong (wrong resource).
            # This should cause the request to fail.
            'author': '/v1/notes/{0}/'.format(
                note_1.pk
            ),
            'title': 'Nopenopenope',
            'slug': 'invalid-request',
            'content': "This shouldn't work.",
            'is_active': True,
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.set_body(json.dumps(data))

        with self.assertRaises(NotFound) as cm:
            nr.post_list(request)

        self.assertEqual(str(cm.exception), "An incorrect URL was provided '/v1/notes/2/' for the 'UserResource' resource.")
        self.assertEqual(Note.objects.count(), 2)


class PrefetchRelatedTests(TestCase):
    def setUp(self):
        self.forum = Forum.objects.create()
        self.resource = api.canonical_resource_for('forum')

        self.user_data = [
            {
                'username': 'valid but unique',
                'email': 'valid.unique@exmaple.com',
                'password': 'junk',
            },
            {
                'username': 'valid and very unique',
                'email': 'valid.very.unique@exmaple.com',
                'password': 'junk',
            },
            {
                'username': 'valid again',
                'email': 'valid.very.unique@exmaple.com',
                'password': 'junk',
            },
        ]

    def tearDown(self):
        usernames = [data['username'] for data in self.user_data]
        User.objects.filter(username__in=usernames).delete()
        self.forum.delete()

    def make_request(self, method):
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = method
        request.set_body(json.dumps({
            'members': [
                self.user_data[0],
                self.user_data[1],
            ],
            'moderators': [self.user_data[2]],
        }))
        request.path = reverse('api_dispatch_detail', kwargs={
            'pk': self.forum.pk,
            'resource_name': self.resource._meta.resource_name,
            'api_name': self.resource._meta.api_name
        })

        return request

    def test_m2m_put(self):
        request = self.make_request('PUT')
        response = self.resource.put_detail(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))

        # Check that the query does what it's supposed to
        # and only the return value is wrong
        self.assertEqual(User.objects.count(), 3)

        self.assertEqual(len(data['members']), 2)
        self.assertEqual(len(data['moderators']), 1)

    def test_m2m_patch(self):
        request = self.make_request('PATCH')
        response = self.resource.patch_detail(request)

        self.assertEqual(response.status_code, 202)
        data = json.loads(response.content.decode('utf-8'))

        # Check that the query does what it's supposed to
        # and only the return value is wrong
        self.assertEqual(User.objects.count(), 3)

        self.assertEqual(len(data['members']), 2)
        self.assertEqual(len(data['moderators']), 1)


class ModelWithReverseItemsRelationshipTest(TestCase):
    def test_reverse_items_relationship(self):
        order_resource = OrderResource()

        data = {
            'name': 'order1',
            'items': [
                {
                    'name': 'car',
                },
                {
                    'name': 'yacht',
                }
            ]
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'

        request.path = reverse('api_dispatch_list',
                               kwargs={'resource_name': order_resource._meta.resource_name,
                                       'api_name': order_resource._meta.api_name})
        request.set_body(json.dumps(data))
        resp = order_resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 2)


class OneToOneTestCase(TestCase):
    def test_reverse_one_to_one_post(self):
        ed = ExtraData.objects.create(name='ed_name')
        resource = TagResource()

        # Post the extradata element which is attached to a "reverse" OneToOne
        request = MockRequest()
        request.method = "POST"
        request.body = json.dumps({
            "name": "tag_name",
            "tagged": [],
            "extradata": "/v1/extradata/%s/" % ed.pk
        })

        resp = resource.post_list(request)
        # Assert that the status code is CREATED
        self.assertEqual(resp.status_code, 201)

        tag = Tag.objects.get(pk=int(resp['Location'].split("/")[-2]))
        self.assertEqual(tag.extradata, ed)

    @staticmethod
    def patch_details(resource, pk, **kwargs):
        # Post the extradata element which is attached to a "reverse" OneToOne
        request = MockRequest()
        request.method = "PATCH"
        request.body = json.dumps(kwargs)
        response = resource.patch_detail(request, pk=pk)
        return response

    def test_one_to_one_two_patches_in_a_row(self):
        resource = TagResource()
        ed = ExtraData.objects.create(name='ed_name')
        tag = Tag.objects.create(name='tag_name')
        tag2 = Tag.objects.create(name="tag_name2")
        extra_data = "/v1/extradata/%s/" % ed.pk

        self.patch_details(resource, tag.pk, extradata=extra_data)
        resp = self.patch_details(resource, tag2.pk, name="new_tag_name")

        self.assertEqual(resp.status_code, 202)
        self.assertEqual(Tag.objects.get(pk=tag2.pk).name, "new_tag_name")

    def test_toonefield_spanning_a_relationship(self):
        """
        #1446
        """
        # just need to be able to add this to a class
        class CustomPersonResource(PersonResource):
            company_address = fields.ToOneField(AddressResource,
                'company__address', null=True, full=True)
        resource = CustomPersonResource()
        resource.fields['company_address']
