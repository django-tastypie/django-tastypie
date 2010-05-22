from django.http import HttpResponse


class TastyPieError(Exception):
    """A base exception for other tastypie-related errors."""
    pass


class HydrationError(TastyPieError):
    """Raised when there is an error hydrating data."""
    pass


class NotRegistered(TastyPieError):
    """
    Raised when the requested resource isn't registered with the ``Api`` class.
    """
    pass


class NotFound(TastyPieError):
    """
    Raised when the resource/object in question can't be found.
    """
    pass


class ApiFieldError(TastyPieError):
    """
    Raised when there is a configuration error with a ``ApiField``.
    """
    pass


class UnsupportedFormat(TastyPieError):
    """
    Raised when an unsupported serialization format is requested.
    """
    pass


class BadRequest(TastyPieError):
    """
    A generalized exception for indicating incorrect request parameters.
    
    Handled specially in that the message tossed by this exception will be
    presented to the end user.
    """
    pass


class BlueberryFillingFound(TastyPieError):
    pass


class InvalidFilterError(TastyPieError):
    """
    Raised when the end user attempts to use a filter that has not be
    explicitly allowed.
    """
    pass


class InvalidSortError(TastyPieError):
    """
    Raised when the end user attempts to sort on a field that has not be
    explicitly allowed.
    """
    pass


class ImmediateHttpResponse(TastyPieError):
    """
    This exception is used to interrupt the flow of processing to immediately
    return a custom HttpResponse.
    
    Common uses include::
    
        * for authentication (like digest/OAuth)
        * for throttling
    
    """
    response = HttpResponse("Nothing provided.")
    
    def __init__(self, response):
        self.response = response
