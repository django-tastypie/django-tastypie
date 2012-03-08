from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ALL
from tastypie.contrib.gis.resources import ModelResource
from tastypie.authorization import Authorization
from gis.models import GeoNote


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        authorization = Authorization()


class GeoNoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        resource_name = 'geonotes'
        queryset = GeoNote.objects.all()
        authorization = Authorization()
        filtering = {
            'points': ALL,
            'lines': ALL,
            'polys': ALL,
        }
