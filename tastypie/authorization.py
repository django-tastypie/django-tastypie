from tastypie.exceptions import TastypieError, Unauthorized


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

        REMOVE BEFORE 1.0
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
        raise NotImplementedError("Tastypie has not way to determine if all objects should be allowed to be created.")

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
        return False

    def update_list(self, object_list, bundle):
        return []

    def update_detail(self, object_list, bundle):
        return False

    def delete_list(self, object_list, bundle):
        return []

    def delete_detail(self, object_list, bundle):
        return False


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
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return False

        # GET-style methods are always allowed.
        return True

    def read_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            return False

        # GET-style methods are always allowed.
        return True

    def create_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return False

        permission = '%s.add_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)

    def create_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            return False

        permission = '%s.add_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)

    def update_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.request, object_list.model)

        if klass is False:
            return False

        permission = '%s.change_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)

    def update_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            return False

        permission = '%s.change_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)

    def delete_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return False

        permission = '%s.delete_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)

    def delete_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            return False

        permission = '%s.delete_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)
