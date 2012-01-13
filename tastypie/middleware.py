from django.contrib.session.middleware import SessionMiddleware


class ApiSessionOptions(object):
    def __init__(self):
        self.suppress_session = False


class ApiSessionMiddleware(SessionMiddleware):
    """
    Piggybacks on django.contrib.session.middleware.SessionMiddleware
    to suppress sessions if the API is being accessd.

    Suppressing sessions may be necessary if sessions are enabled
    elsewhere on the site. Active sessions use the `Vary: Cookie`
    header, which may not allow upstream caching to work correctly.
    """
    def process_request(self, request):
        request.tastypie = ApiSessionOptions()
        return super(ApiSessionMiddleware).process_request(request)
        
    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie.

        If an API resource requests the suppression of sessions, do so.
        """
        try:
            suppress_session = request.tastypie.suppress_session
        except AttributeError:
            pass
        else:
            if not suppress_session:
                response = super(ApiSessionMiddleware).process_response(request, response)

        return response
