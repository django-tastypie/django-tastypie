import cProfile
import pstats

from django.contrib.auth.models import User
from django.test import TestCase

import six

from core.tests.mocks import MockRequest

from .models import Note
from .resources import NoteResource


class ProfilingTestCase(TestCase):
    def setUp(self):
        self.pr = cProfile.Profile()
        self.pr.enable()

    def tearDown(self):
        p = pstats.Stats(self.pr)
        # p.strip_dirs()
        p.sort_stats('tottime')
        p.print_stats(75)


class ResourceProfilingTestCase(ProfilingTestCase):
    def setUp(self):
        self.resource = NoteResource()
        self.request = MockRequest()
        self.request.path = '/api/v1/notes/'
        self.request.GET = {'limit': '100'}

        user = User.objects.create_user('foo', 'pass')

        for i in six.xrange(0, 200):
            Note.objects.create(author=user, title='Note #%s' % i,
                slug='note-%s' % i)

        super(ResourceProfilingTestCase, self).setUp()

    def test_get_list(self):
        get_list = self.resource.get_list
        request = self.request

        for i in six.xrange(0, 50):
            get_list(request)
