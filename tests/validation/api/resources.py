from django.contrib.auth.models import User
from tastypie import fields
from tastypie.constants import ALL
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.validation import Validation
from basic.models import Note


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        authorization = Authorization()


class NoteValidation(Validation):

    def is_update_valid(self, bundle, request=None):
        " Check if then update is valid."

        if not bundle.data:
            return {'__all__': ['We need some data.']}

        if 'content' not in bundle.data:
            return {'content': ["We need the new content."]}
        else:
            if len(bundle.obj.content) < len(bundle.data['content']):
                return {'content': ["New content must be shorter."]}

        return {}

    def is_valid(self, bundle, request=None):
        "Check that note doesn't exceed 40 characters"
        if not bundle.data:
            return {'__all__': ['We need some data.']}

        if 'content' in bundle.data:
            if len(bundle.data['content']) > 40:
                return {'content': ["Note must not exceed the 40 characters."]}

        return {}


class NoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()
        filtering = {
            "created": ALL
            }
        validation = NoteValidation()
