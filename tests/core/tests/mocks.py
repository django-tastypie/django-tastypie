class MockRequest(object):
    def __init__(self):
        self.GET = {}
        self.POST = {}
        self.PUT = {}
        self.DELETE = {}
        self.META = {}
