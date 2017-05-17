from functools import wraps


def custom_api(allowed=None):
    """
    Decorator for customized api end point that does method check,
    authentication and throttle_check.

    Takes an ``allowed`` parameter, which should be a list of lowercase HTTP
    methods to check against.

    The func should return a dict as result data.
    """
    def _custom_api_decorator(func):
        @wraps(func)
        def _wrapper(self, request, **kwargs):
            self.method_check(request, allowed=allowed)
            self.is_authenticated(request)
            self.throttle_check(request)

            result = func(self, request, **kwargs)

            self.log_throttled_access(request)
            return self.create_response(request, result)
        return _wrapper
    return _custom_api_decorator
