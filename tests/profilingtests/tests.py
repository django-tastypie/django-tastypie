import cProfile
import pstats

from django.test import TestCase

from core.models import Note
from core.tests.mocks import MockRequest
from core.tests.resources import NoteResource


class ProfilingTestCase(TestCase):
    def setUp(self):
        self.pr = cProfile.Profile()
        self.pr.enable()
    
    def tearDown(self):
        p = pstats.Stats (self.pr)
        p.strip_dirs()
        p.sort_stats('cumtime')
        p.print_stats()

class ResourceProfilingTestCase(ProfilingTestCase):
    def setUp(self):
        self.resource = NoteResource()
        self.request = MockRequest()
        self.request.path = '/api/v1/notes/'
        self.request.GET = {'limit': '100'}
        
        for i in xrange(0, 200):
            Note.objects.create(title='Note #%s' % i, slug='note-%s' % i)
        
        super(ResourceProfilingTestCase, self).setUp()
    
    def test_get_list(self):
        get_list = self.resource.get_list
        request = self.request
        
        for i in xrange(0, 250):
            get_list(request)
