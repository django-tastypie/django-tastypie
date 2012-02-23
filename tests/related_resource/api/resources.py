from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from core.models import Note, MediaBit
from related_resource.models import Category, Tag, ExtraData, Taggable, TaggableTag, Company, Person, Dog, DogHouse


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        allowed_methods = ['get']


class NoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author')

    class Meta:
        resource_name = 'notes'
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
    media_bits = fields.ToManyField('related_resource.api.resources.FreshMediaBitResource', 'media_bits', related_name='note')

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


class CompanyResource(ModelResource):
    employees = fields.ToManyField('related_resource.api.resources.PersonResource', 'employees', full=True, related_name='company')

    class Meta:
        queryset = Company.objects.all()
        resource_name = 'company'
        authorization = Authorization()


class PersonResource(ModelResource):
    company = fields.ToOneField(CompanyResource, 'company')
    dogs = fields.ToManyField('related_resource.api.resources.DogResource', 'dogs', full=True, related_name='owner')

    class Meta:
        queryset = Person.objects.all()
        resource_name = 'person'
        authorization = Authorization()


class DogHouseResource(ModelResource):
    class Meta:
        queryset = DogHouse.objects.all()
        resource_name = 'doghouse'
        authorization = Authorization()


class DogResource(ModelResource):
    owner = fields.ToOneField(PersonResource, 'owner')
    house = fields.ToOneField(DogHouseResource, 'house', full=True)

    class Meta:
        queryset = Dog.objects.all()
        resource_name = 'dog'
        authorization = Authorization()
