from django.contrib.auth.models import User

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization

from core.models import Note, MediaBit

from related_resource.models import Bone, Category, Contact, ContactGroup,\
    ExtraData, Person, Company, Product, Address, Dog, DogHouse, Forum,\
    Job, Label, Order, OrderItem, Payment, Post, Tag, Taggable, TaggableTag


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()


class UpdatableUserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        allowed_methods = ['get', 'put']
        authorization = Authorization()


class NoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author')

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()


class NoteWithUpdatableUserResource(ModelResource):
    author = fields.ForeignKey(UpdatableUserResource, 'author')

    class Meta:
        resource_name = 'noteswithupdatableuser'
        queryset = Note.objects.all()
        authorization = Authorization()


class CategoryResource(ModelResource):
    parent = fields.ToOneField('self', 'parent', null=True)

    class Meta:
        resource_name = 'category'
        queryset = Category.objects.all()
        authorization = Authorization()


class TagResource(ModelResource):
    taggabletags = fields.ToManyField(
        'related_resource.api.resources.TaggableTagResource', 'taggabletags',
        null=True)

    extradata = fields.ToOneField(
        'related_resource.api.resources.ExtraDataResource', 'extradata',
        null=True, blank=True, full=True)

    class Meta:
        resource_name = 'tag'
        queryset = Tag.objects.all()
        authorization = Authorization()


class TaggableResource(ModelResource):
    taggabletags = fields.ToManyField(
        'related_resource.api.resources.TaggableTagResource', 'taggabletags',
        null=True)

    class Meta:
        resource_name = 'taggable'
        queryset = Taggable.objects.all()
        authorization = Authorization()


class TaggableTagResource(ModelResource):
    tag = fields.ToOneField(
        'related_resource.api.resources.TagResource', 'tag',
        null=True)
    taggable = fields.ToOneField(
        'related_resource.api.resources.TaggableResource', 'taggable',
        null=True)

    class Meta:
        resource_name = 'taggabletag'
        queryset = TaggableTag.objects.all()
        authorization = Authorization()


class ExtraDataResource(ModelResource):
    tag = fields.ToOneField(
        'related_resource.api.resources.TagResource', 'tag',
        null=True)

    class Meta:
        resource_name = 'extradata'
        queryset = ExtraData.objects.all()
        authorization = Authorization()


class FreshNoteResource(ModelResource):
    media_bits = fields.ToManyField(
        'related_resource.api.resources.FreshMediaBitResource', 'media_bits',
        related_name='note')

    class Meta:
        queryset = Note.objects.all()
        resource_name = 'freshnote'
        authorization = Authorization()


class FreshMediaBitResource(ModelResource):
    note = fields.ToOneField(FreshNoteResource, 'note')

    class Meta:
        queryset = MediaBit.objects.all()
        resource_name = 'freshmediabit'
        authorization = Authorization()


class AddressResource(ModelResource):
    class Meta:
        queryset = Address.objects.all()
        resource_name = 'address'
        authorization = Authorization()


class ProductResource(ModelResource):
    producer = fields.ToOneField(
        'related_resource.api.resources.CompanyResource', 'producer')

    class Meta:
        queryset = Product.objects.all()
        resource_name = 'product'
        authorization = Authorization()


class CompanyResource(ModelResource):
    address = fields.ToOneField(AddressResource, 'address', null=True,
        full=True)
    products = fields.ToManyField(ProductResource, 'products', full=True,
        related_name='producer', null=True)

    class Meta:
        queryset = Company.objects.all()
        resource_name = 'company'
        authorization = Authorization()


class PersonResource(ModelResource):
    company = fields.ToOneField(CompanyResource, 'company', null=True,
        full=True)
    dogs = fields.ToManyField('related_resource.api.resources.DogResource',
        'dogs', full=True, related_name='owner', null=True)

    class Meta:
        queryset = Person.objects.all()
        resource_name = 'person'
        authorization = Authorization()


class DogHouseResource(ModelResource):
    class Meta:
        queryset = DogHouse.objects.all()
        resource_name = 'doghouse'
        authorization = Authorization()


class BoneResource(ModelResource):
    dog = fields.ToOneField('related_resource.api.resources.DogResource',
        'dog', null=True)

    class Meta:
        queryset = Bone.objects.all()
        resource_name = 'bone'
        authorization = Authorization()


class DogResource(ModelResource):
    owner = fields.ToOneField(PersonResource, 'owner')
    house = fields.ToOneField(DogHouseResource, 'house', full=True, null=True)
    bones = fields.ToManyField(BoneResource, 'bones', full=True, null=True,
        related_name='dog')

    class Meta:
        queryset = Dog.objects.all()
        resource_name = 'dog'
        authorization = Authorization()


class LabelResource(ModelResource):
    class Meta:
        resource_name = 'label'
        queryset = Label.objects.all()
        authorization = Authorization()


class PostResource(ModelResource):
    label = fields.ToManyField(LabelResource, 'label', null=True)

    class Meta:
        queryset = Post.objects.all()
        resource_name = 'post'
        authorization = Authorization()


class PaymentResource(ModelResource):
    job = fields.ToOneField('related_resource.api.resources.JobResource',
        'job')

    class Meta:
        queryset = Payment.objects.all()
        resource_name = 'payment'
        authorization = Authorization()
        allowed_methods = ('get', 'put', 'post')


class JobResource(ModelResource):
    payment = fields.ToOneField(PaymentResource, 'payment', related_name='job')

    class Meta:
        queryset = Job.objects.all()
        resource_name = 'job'
        authorization = Authorization()
        allowed_methods = ('get', 'put', 'post')


class ForumResource(ModelResource):
    moderators = fields.ManyToManyField(UserResource, 'moderators', full=True)
    members = fields.ManyToManyField(UserResource, 'members', full=True)

    class Meta:
        resource_name = 'forum'
        queryset = Forum.objects.prefetch_related('moderators', 'members')
        authorization = Authorization()
        always_return_data = True


class OrderItemResource(ModelResource):
    order = fields.ForeignKey("related_resource.api.resources.OrderResource", "order")

    class Meta:
        queryset = OrderItem.objects.all()
        resource_name = 'orderitem'
        authorization = Authorization()


class OrderResource(ModelResource):
    items = fields.ToManyField("related_resource.api.resources.OrderItemResource", "items",
                               related_name="order", full=True)

    class Meta:
        queryset = Order.objects.all()
        resource_name = 'order'
        authorization = Authorization()


class ContactGroupResource(ModelResource):
    members = fields.ToManyField('related_resource.api.resources.ContactResource', 'members', related_name='groups', null=True, blank=True)

    class Meta:
        queryset = ContactGroup.objects.prefetch_related('members')
        resource_name = 'contactgroup'
        authorization = Authorization()


class ContactResource(ModelResource):
    groups = fields.ToManyField(ContactGroupResource, 'groups', related_name='members', null=True, blank=True)

    class Meta:
        queryset = Contact.objects.prefetch_related('groups')
        resource_name = 'contact'
        authorization = Authorization()
