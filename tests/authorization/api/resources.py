from django.contrib.auth.models import User
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie import fields
from tastypie.resources import ModelResource
from authorization.models import Note

import logging

logger = logging.getLogger(__name__)


class UserObjectAuthorization(object):
    """
    Only authorize objects where request.user matches obj.user field.

    In real world application, objects would have row level permissions
    applied to them using tools like django-guardian. For simplicity,
    this demo assumes that the object has a `user` field.
    """
    def base_checks(self, request, model_klass):
        # If it doesn't look like a model, we can't check permissions.
        if not model_klass or not getattr(model_klass, '_meta', None):
            return False

        # User must be logged in to check permissions.
        if not hasattr(request, 'user'):
            return False

        return model_klass

    def read_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return False
        if bundle.request.user.is_anonymous():
            return object_list.none()
        return object_list.filter(user=bundle.request.user)

    def read_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            return False

        if bundle.request.user == bundle.obj.user:
            return True
        else:
            raise Unauthorized()

    def create_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return False
        if bundle.request.user.is_anonymous():
            return object_list.none()
        return object_list

    def create_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            return False
        if bundle.request.user.is_anonymous():
            raise Unauthorized()
        return True

    def update_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.request, object_list.model)

        if klass is False:
            return False
        if bundle.request.user.is_anonymous():
            return object_list.none()
        return object_list.filter(user=bundle.request.user)

    def update_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            return False

        if bundle.request.user == bundle.obj.user:
            return True
        else:
            raise Unauthorized()

    def delete_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return False

        if bundle.request.user.is_anonymous():
            return object_list.none()
        return object_list.filter(user=bundle.request.user)

    def delete_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            return False

        if bundle.request.user == bundle.obj.user:
            return True
        else:
            raise Unauthorized()


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
        authorization = UserObjectAuthorization()

    def obj_create(self, bundle, request=None, **kwargs):
        """
        Making request.user owner of the new note.
        """
        bundle = super(NoteResource, self).obj_create(bundle, request, user=request.user, **kwargs)

        return bundle
