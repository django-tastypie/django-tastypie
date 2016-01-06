from __future__ import unicode_literals

import settings

from tastypie.exceptions import TastypieError, Unauthorized
from tastypie.compat import get_module_name


class Authorization(object):
    """
    A base class that provides no permissions checking.
    """
    def __get__(self, instance, owner):
        """
        Makes ``Authorization`` a descriptor of ``ResourceOptions`` and creates
        a reference to the ``ResourceOptions`` object that may be used by
        methods of ``Authorization``.
        """
        self.resource_meta = instance
        return self

    def apply_limits(self, request, object_list):
        """
        Deprecated.

        FIXME: REMOVE BEFORE 1.0
        """
        raise TastypieError("Authorization classes no longer support `apply_limits`. Please update to using `read_list`.")

    def read_list(self, object_list, bundle):
        """
        Returns a list of all the objects a user is allowed to read.

        Should return an empty list if none are allowed.

        Returns the entire list by default.
        """
        return object_list

    def read_detail(self, object_list, bundle):
        """
        Returns either ``True`` if the user is allowed to read the object in
        question or throw ``Unauthorized`` if they are not.

        Returns ``True`` by default.
        """
        return True

    def create_list(self, object_list, bundle):
        """
        Unimplemented, as Tastypie never creates entire new lists, but
        present for consistency & possible extension.
        """
        raise NotImplementedError("Tastypie has no way to determine if all objects should be allowed to be created.")

    def create_detail(self, object_list, bundle):
        """
        Returns either ``True`` if the user is allowed to create the object in
        question or throw ``Unauthorized`` if they are not.

        Returns ``True`` by default.
        """
        return True

    def update_list(self, object_list, bundle):
        """
        Returns a list of all the objects a user is allowed to update.

        Should return an empty list if none are allowed.

        Returns the entire list by default.
        """
        return object_list

    def update_detail(self, object_list, bundle):
        """
        Returns either ``True`` if the user is allowed to update the object in
        question or throw ``Unauthorized`` if they are not.

        Returns ``True`` by default.
        """
        return True

    def delete_list(self, object_list, bundle):
        """
        Returns a list of all the objects a user is allowed to delete.

        Should return an empty list if none are allowed.

        Returns the entire list by default.
        """
        return object_list

    def delete_detail(self, object_list, bundle):
        """
        Returns either ``True`` if the user is allowed to delete the object in
        question or throw ``Unauthorized`` if they are not.

        Returns ``True`` by default.
        """
        return True


class ReadOnlyAuthorization(Authorization):
    """
    Default Authentication class for ``Resource`` objects.

    Only allows ``GET`` requests.
    """
    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        return []

    def create_detail(self, object_list, bundle):
        raise Unauthorized("You are not allowed to access that resource.")

    def update_list(self, object_list, bundle):
        return []

    def update_detail(self, object_list, bundle):
        raise Unauthorized("You are not allowed to access that resource.")

    def delete_list(self, object_list, bundle):
        return []

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("You are not allowed to access that resource.")


class DjangoAuthorization(Authorization):
    """
    Uses permission checking from ``django.contrib.auth`` to map
    ``POST / PUT / DELETE / PATCH`` to their equivalent Django auth
    permissions.

    Both the list & detail variants simply check the model they're based
    on, as that's all the more granular Django's permission setup gets.
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
        # By default, follows `ModelAdmin` "convention" to use `app.change_model`
        # `django.contrib.auth.models.Permission` for both viewing and updating.
        # https://docs.djangoproject.com/es/1.9/topics/auth/default/#permissions-and-authorization

        return self.update_list(object_list, bundle)

    def read_detail(self, object_list, bundle):
        return self.update_detail(object_list, bundle)

    def create_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.add_%s' % (
            klass._meta.app_label,
            get_module_name(klass._meta)
        )

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def create_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.add_%s' % (
            klass._meta.app_label,
            get_module_name(klass._meta)
        )

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def update_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.change_%s' % (
            klass._meta.app_label,
            get_module_name(klass._meta)
        )

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def update_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.change_%s' % (
            klass._meta.app_label,
            get_module_name(klass._meta)
        )

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def delete_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.delete_%s' % (
            klass._meta.app_label,
            get_module_name(klass._meta)
        )

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def delete_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.delete_%s' % (
            klass._meta.app_label,
            get_module_name(klass._meta)
        )

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True


class DjangoObjectAuthorization(Authorization):
    '''
    Uses permission checking from ``django.contrib.auth`` to map
    ``POST / PUT / DELETE / PATCH`` to their equivalent Django auth
    permissions.

    Both the list & detail simply check the object they're based on.
    Object level authorization api is added since django 1.5. However,
    it will default to no-access unless an AUTHENTICATION_BACKENDS is
    setup to handle those checks.
    '''

    # By default, follows `ModelAdmin` "convention" to use `app.change_model`
    # `django.contrib.auth.models.Permission` for both viewing and updating.
    # https://docs.djangoproject.com/es/1.9/topics/auth/default/#permissions-and-authorization
    READ_PERM_CODE = getattr(settings, 'TASTYPIE_READ_PERM_CODE', 'change')

    def base_checks(self, request, model_klass):
        # If it doesn't look like a model, we can't check permissions.
        if not model_klass or not getattr(model_klass, '_meta', None):
            return False

        # User must be logged in to check permissions.
        if not hasattr(request, 'user'):
            return False

        return model_klass

    def perm_list_checks(self, request, code, obj_list):
        klass = self.base_checks(request, obj_list.model)
        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.%s_%s' % (
            klass._meta.app_label,
            code,
            get_module_name(klass._meta)
        )

        if request.user.has_perm(permission, obj_list):
            return obj_list

        return obj_list.none()

    def perm_obj_checks(self, request, code, obj):
        klass = self.base_checks(request, obj.__class__)
        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.%s_%s' % (
            klass._meta.app_label,
            code,
            get_module_name(klass._meta)
        )

        if request.user.has_perm(permission, obj):
            return True

        return False

    def read_list(self, object_list, bundle):
        return self.perm_list_checks(bundle.request, self.READ_PERM_CODE, object_list)

    def read_detail(self, object_list, bundle):
        return self.perm_obj_checks(bundle.request, self.READ_PERM_CODE, bundle.obj)

    def create_list(self, object_list, bundle):
        return self.perm_list_checks(bundle.request, 'add', object_list)

    def create_detail(self, object_list, bundle):
        return self.perm_obj_checks(bundle.request, 'add', bundle.obj)

    def update_list(self, object_list, bundle):
        return self.perm_list_checks(bundle.request, 'change', object_list)

    def update_detail(self, object_list, bundle):
        return self.perm_obj_checks(bundle.request, 'change', bundle.obj)

    def delete_list(self, object_list, bundle):
        return self.perm_list_checks(bundle.request, 'delete', object_list)

    def delete_detail(self, object_list, bundle):
        return self.perm_obj_checks(bundle.request, 'delete', bundle.obj)
