from django.http import HttpResponse


class TastyPieError(Exception):
    pass


class HydrationError(TastyPieError):
    pass


class NotRegistered(TastyPieError):
    pass


class URLReverseError(TastyPieError):
    pass


class NotFound(TastyPieError):
    pass


class ApiFieldError(TastyPieError):
    pass


class UnsupportedFormat(TastyPieError):
    pass


class BadRequest(TastyPieError):
    pass


class BlueberryFillingFound(TastyPieError):
    pass


class InvalidFilterError(TastyPieError):
    pass


class InvalidSortError(TastyPieError):
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
