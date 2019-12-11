import json

from contextlib import contextmanager

from django.test.testcases import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connections


class TastyPieTestCase(TestCase):

    @contextmanager
    def withAssertNumQueriesLessThan(self, value, using='default', verbose=False):
        with CaptureQueriesContext(connections[using]) as context:
            yield   # your test will be run here
        if verbose:
            msg = "\r\n%s" % json.dumps(context.captured_queries, indent=4)
        else:
            msg = None
        self.assertLess(context.final_queries, value, msg=msg)


class TestCaseWithFixture(TastyPieTestCase):
    fixtures = ['test_data.json']
