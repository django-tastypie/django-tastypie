import operator


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

    def is_authorized(self, request, object=None):
        """
        Checks if the user is authorized to perform the request. If ``object``
        is provided, it can do additional row-level checks.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        return True


class ReadOnlyAuthorization(Authorization):
    """
    Default Authentication class for ``Resource`` objects.

    Only allows GET requests.
    """

    def is_authorized(self, request, object=None):
        """
        Allow any ``GET`` request.
        """
        if request.method == 'GET':
            return True
        else:
            return False


class DjangoAuthorization(Authorization):
    """
    Uses permission checking from ``django.contrib.auth`` to map
    ``POST / PUT / DELETE / PATCH`` to their equivalent Django auth
    permissions.
    """
    def is_authorized(self, request, object=None):
        # GET-style methods are always allowed.
        if request.method in ('GET', 'OPTIONS', 'HEAD'):
            return True

        klass = self.resource_meta.object_class

        # If it doesn't look like a model, we can't check permissions.
        if not klass or not getattr(klass, '_meta', None):
            return True

        permission_map = {
            'POST': ['%s.add_%s'],
            'PUT': ['%s.change_%s'],
            'DELETE': ['%s.delete_%s'],
            'PATCH': ['%s.add_%s', '%s.change_%s', '%s.delete_%s'],
        }
        permission_codes = []

        # If we don't recognize the HTTP method, we don't know what
        # permissions to check. Deny.
        if request.method not in permission_map:
            return False

        for perm in permission_map[request.method]:
            permission_codes.append(perm % (klass._meta.app_label, klass._meta.module_name))

        # User must be logged in to check permissions.
        if not hasattr(request, 'user'):
            return False

        return request.user.has_perms(permission_codes)
