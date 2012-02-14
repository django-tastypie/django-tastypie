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
        A means of narrowing a list of objects on a per-user/request basis.

        Default simply returns the unaltered list.
        """
        return object_list

    def to_read(self, bundle):
        """
        Checks if the user is authorized to perform the request. If ``object``
        is provided, it can do additional row-level checks.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        return True

    def to_add(self, bundle):
        return True

    def to_change(self, bundle):
        return True

    def to_delete(self, bundle):
        return True


class ReadOnlyAuthorization(Authorization):
    """
    Default Authentication class for ``Resource`` objects.

    Only allows ``GET`` requests.
    """
    def to_read(self, bundle):
        return True

    def to_add(self, bundle):
        return False

    def to_change(self, bundle):
        return False

    def to_delete(self, bundle):
        return False


class DjangoAuthorization(Authorization):
    """
    Uses permission checking from ``django.contrib.auth`` to map
    ``POST / PUT / DELETE / PATCH`` to their equivalent Django auth
    permissions.
    """
    def base_checks(self, bundle):
        klass = self.resource_meta.object_class

        # If it doesn't look like a model, we can't check permissions.
        if not klass or not getattr(klass, '_meta', None):
            return False

        # User must be logged in to check permissions.
        if not hasattr(bundle.request, 'user'):
            return False

        return klass

    def to_read(self, bundle):
        klass = self.base_checks(bundle)

        if klass is False:
            return False

        # GET-style methods are always allowed.
        return True

    def to_add(self, bundle):
        klass = self.base_checks(bundle)

        if klass is False:
            return False

        permission = '%s.add_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)

    def to_change(self, bundle):
        klass = self.base_checks(bundle)

        if klass is False:
            return False

        permission = '%s.change_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)

    def to_delete(self, bundle):
        klass = self.base_checks(bundle)

        if klass is False:
            return False

        permission = '%s.delete_%s' % (klass._meta.app_label, klass._meta.module_name)
        return bundle.request.user.has_perm(permission)
