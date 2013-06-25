import django

class MockRequest(object):
    def __init__(self):
        self.GET = {}
        self.POST = {}
        self.PUT = {}
        self.DELETE = {}
        self.META = {}
        self.path = ''
        self.method = 'GET'
    
    def get_full_path(self, *args, **kwargs):
        return self.path
    
    def is_ajax(self):
        return self.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    def set_body(self, content):
        if django.VERSION >= (1, 4):
            body_attr = "body"
        else:
            body_attr = "raw_post_data"

        setattr(self, body_attr, content)