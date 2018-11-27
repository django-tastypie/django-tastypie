class MockRequest(object):
    def __init__(self):
        self.GET = {}
        self.POST = {}
        self.PUT = {}
        self.DELETE = {}
        self.META = {}
        self.path = ''
        self.method = 'GET'

    def _load_post_and_files(self, *args, **kwargs):
        pass

    def get_full_path(self, *args, **kwargs):
        return self.path

    def is_ajax(self):
        return self.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    def set_body(self, content):
        self.body = content
