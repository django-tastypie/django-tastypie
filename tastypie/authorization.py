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

    def __and__(a,b):
        return IntersectionAuthorization(a,b)

    def __or__(a,b):
        return UnionAuthorization(a,b)


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
    Uses permission checking from ``django.contrib.auth`` to map ``POST``,
    ``PUT``, and ``DELETE`` to their equivalent django auth permissions.
    """
    def is_authorized(self, request, object=None):
        # GET is always allowed
        if request.method == 'GET':
            return True

        klass = self.resource_meta.object_class

        # cannot check permissions if we don't know the model
        if not klass or not getattr(klass, '_meta', None):
            return True

        permission_codes = {
            'POST': '%s.add_%s',
            'PUT': '%s.change_%s',
            'DELETE': '%s.delete_%s',
        }

        # cannot map request method to permission code name
        if request.method not in permission_codes:
            return True

        permission_code = permission_codes[request.method] % (
            klass._meta.app_label,
            klass._meta.module_name)

        # user must be logged in to check permissions
        # authentication backend must set request.user
        if not hasattr(request, 'user'):
            return False

        return request.user.has_perm(permission_code)

class IntersectionAuthorization(Authorization):
    """
    Checks that all the provided Authorization methods are authorized
    """
    def __init__(self, *backends, **kwargs):
        super(Authorization, self).__init__(**kwargs)
        self.backends = backends

    def is_authorized(self, request, object=None):
        # Intersection method
        for backend in self.backends:
            authorized = backend.is_authorized(request, object)
            if not authorized:
                return False
        return True

    def apply_limits(self, request, object_list):
        backends = [b for b in self.backends if hasattr(b, 'apply_limits')]
        if len(backends) == 0:
            return object_list

        result = backends[0].apply_limits(request, object_list)
        for backend in backends[1:]:
            result = result & backend.apply_limits(request, backend.apply_limits(request, object_list))
        return result

class UnionAuthorization(Authorization):
    """
    Checks that any of the provided Authorization methods are authorized
    """
    def __init__(self, *backends, **kwargs):
        super(Authorization, self).__init__(**kwargs)
        self.backends = backends

    def is_authorized(self, request, object=None):
        # Union method
        for backend in self.backends:
            authorized = backend.is_authorized(request, object)
            if authorized:
                return True
        return False

    def apply_limits(self, request, object_list):
        backends = [b for b in self.backends if hasattr(b, 'apply_limits')]
        if len(backends) == 0:
            return object_list

        result = backends[0].apply_limits(request, object_list)
        for backend in backends[1:]:
            result = result | backend.apply_limits(request, object_list)
        return result
