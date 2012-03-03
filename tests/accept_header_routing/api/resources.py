from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from accept_header_routing.models import Note, Business, Organization


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        authorization = Authorization()


class NoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()


class NoteResource2(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()

    def dehydrate(self, bundle):
        bundle.data['custom_field'] = "Whatever you want"
        return bundle


class BusinessResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        resource_name = 'businesses'
        queryset = Business.objects.all()
        authorization = Authorization()


class OrganizationResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        resource_name = 'organizations'
        queryset = Organization.objects.all()
        authorization = Authorization()
