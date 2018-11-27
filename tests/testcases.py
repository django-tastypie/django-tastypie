from django.test.testcases import TestCase


class TestCaseWithFixture(TestCase):
    fixtures = ['test_data.json']
