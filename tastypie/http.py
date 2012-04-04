"""
The various HTTP responses for use in returning proper HTTP codes.
"""
from django.http import HttpResponse

class HttpErrorResponse(HttpResponse):
    pass


class HttpCreated(HttpResponse):
    status_code = 201

    def __init__(self, *args, **kwargs):
        location = ''

        if 'location' in kwargs:
            location = kwargs['location']
            del(kwargs['location'])

        super(HttpCreated, self).__init__(*args, **kwargs)
        self['Location'] = location


class HttpAccepted(HttpResponse):
    status_code = 202


class HttpNoContent(HttpResponse):
    status_code = 204


class HttpMultipleChoices(HttpResponse):
    status_code = 300


class HttpSeeOther(HttpResponse):
    status_code = 303


class HttpNotModified(HttpResponse):
    status_code = 304


class HttpBadRequest(HttpErrorResponse):
    status_code = 400


class HttpUnauthorized(HttpErrorResponse):
    status_code = 401


class HttpForbidden(HttpErrorResponse):
    status_code = 403


class HttpNotFound(HttpErrorResponse):
    status_code = 404


class HttpMethodNotAllowed(HttpErrorResponse):
    status_code = 405


class HttpConflict(HttpErrorResponse):
    status_code = 409


class HttpGone(HttpErrorResponse):
    status_code = 410


class HttpApplicationError(HttpErrorResponse):
    status_code = 500


class HttpNotImplemented(HttpErrorResponse):
    status_code = 501

