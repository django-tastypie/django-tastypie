from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from core.models import Note
from related_resource.models import Category, Tag, ExtraData, Taggable, TaggableTag


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

