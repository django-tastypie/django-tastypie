from tastypie.exceptions import Unauthorized


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
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        # GET-style methods are always allowed.
        return object_list

    def read_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        # GET-style methods are always allowed.
        return True

    def create_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.add_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def create_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.add_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def update_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.change_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def update_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.change_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def delete_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.delete_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def delete_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.delete_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True


class ObjectAuthorization(Authorization):
    """
        Class provides object authorization.

        This class requires path to field which will be compared to
        authorized user. Or you can pass own function, and compare any object
        which you want.

        How to use this class, see docblock of __init__ method.
    """

    text_unauth = "You are not allowed to access that resource."

    def __init__(self, filter_path="user", func=None):
        """
            :param str filter_path: path to field which will be compared
            :param function func: user's function

            .. note::
                You can pass your function (func arg). Function must return
                field which later will be compared to your filter.
        """
        self.filter_path = filter_path
        self.func = func

    def get_obj_from_path(self, obj):
        for attr in self.filter_path.split("__"):
            obj = obj.__getattribute__(attr)
        return obj

    def get_pk(self, obj):
        """
            Get pk from object.

            :param dict obj: dict object like
                {"owner": "/api/v1/user/1", "name": "MyShop", ...} or
                {"shop": {"owner": {"username": "user_name", ...}, ..}, ..}

            .. note::
                If user doesn't provide required data (KeyError) then raise
                Unauthorized.

                For condition below loop:
                    If object is dict then get value from id key.
                    If object is string like ("/api/v1/shop/1/"), split them
                    filter, and get last value (ID).
        """
        for attr in self.filter_path.split("__"):
            try:
                obj = obj[attr]
            except KeyError:
                raise Unauthorized(self.text_unauth)

        if hasattr(obj, 'keys'):
            obj = obj['id']
        else:
            obj = filter(lambda x: x, obj.split("/"))[-1]

        return int(obj)

    def auth_list(self, object_list, bundle):
        if self.func:
            return object_list.\
                filter(**{self.filter_path: self.func(bundle.request)})
        else:
            return object_list.\
                filter(**{self.filter_path: bundle.request.user})

    def auth_detail(self, object_list, bundle):
        obj_from_path = self.get_obj_from_path(bundle.obj)

        if self.func:
            if not (self.func(bundle.request) == obj_from_path):
                raise Unauthorized(self.text_unauth)
        else:
            if not (bundle.request.user == obj_from_path):
                raise Unauthorized(self.text_unauth)

        return True

    def read_list(self, object_list, bundle):
        return self.auth_list(object_list, bundle)

    def read_detail(self, object_list, bundle):
        return self.auth_detail(object_list, bundle)

    def create_detail(self, object_list, bundle):
        bundle_obj_pk = self.get_pk(bundle.data)

        if self.func and self.func(bundle.request).pk == bundle_obj_pk:
            return True
        elif bundle.request.user.pk == bundle_obj_pk:
            return True

        raise Unauthorized(self.text_unauth)

    def update_list(self, object_list, bundle):
        return self.auth_list(object_list, bundle)

    def update_detail(self, object_list, bundle):
        return self.auth_detail(object_list, bundle)

    def delete_list(self, object_list, bundle):
        return self.auth_list(object_list, bundle)

    def delete_detail(self, object_list, bundle):
        return self.auth_detail(object_list, bundle)
