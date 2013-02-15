from django.http import HttpRequest
from django.test import TestCase

from tastypie.exceptions import BadRequest
from tastypie.serializers import Serializer
from tastypie.utils.mime import determine_format, build_content_type


class MimeTestCase(TestCase):
    def test_build_content_type(self):
        # JSON & JSONP don't include charset.
        self.assertEqual(build_content_type('application/json'), 'application/json')
        self.assertEqual(build_content_type('text/javascript'), 'text/javascript')
        self.assertEqual(build_content_type('application/json', encoding='ascii'), 'application/json')
        # Everything else should.
        self.assertEqual(build_content_type('application/xml'), 'application/xml; charset=utf-8')
        self.assertEqual(build_content_type('application/xml', encoding='ascii'), 'application/xml; charset=ascii')

    def test_determine_format(self):
        serializer = Serializer()
        full_serializer = Serializer(formats=['json', 'jsonp', 'xml', 'yaml', 'html', 'plist'])
        request = HttpRequest()

        # Default.
        self.assertEqual(determine_format(request, serializer), 'application/json')

        # Test forcing the ``format`` parameter.
        request.GET = {'format': 'json'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        # Disabled by default.
        request.GET = {'format': 'jsonp'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        # Explicitly enabled.
        request.GET = {'format': 'jsonp'}
        self.assertEqual(determine_format(request, full_serializer), 'text/javascript')

        request.GET = {'format': 'xml'}
        self.assertEqual(determine_format(request, serializer), 'application/xml')

        request.GET = {'format': 'yaml'}
        self.assertEqual(determine_format(request, serializer), 'text/yaml')

        request.GET = {'format': 'plist'}
        self.assertEqual(determine_format(request, serializer), 'application/x-plist')

        request.GET = {'format': 'foo'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        # Test the ``Accept`` header.
        request.META = {'HTTP_ACCEPT': 'application/json'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        # Again, disabled by default.
        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        # Again, explicitly enabled.
        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        self.assertEqual(determine_format(request, full_serializer), 'text/javascript')

        request.META = {'HTTP_ACCEPT': 'application/xml'}
        self.assertEqual(determine_format(request, serializer), 'application/xml')

        request.META = {'HTTP_ACCEPT': 'text/yaml'}
        self.assertEqual(determine_format(request, serializer), 'text/yaml')

        request.META = {'HTTP_ACCEPT': 'application/x-plist'}
        self.assertEqual(determine_format(request, serializer), 'application/x-plist')

        request.META = {'HTTP_ACCEPT': 'text/html'}
        self.assertEqual(determine_format(request, serializer), 'text/html')

        request.META = {'HTTP_ACCEPT': '*/*'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        request.META = {'HTTP_ACCEPT': 'application/json,application/xml;q=0.9,*/*;q=0.8'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        request.META = {'HTTP_ACCEPT': 'text/plain,application/xml,application/json;q=0.9,*/*;q=0.8'}
        self.assertEqual(determine_format(request, serializer), 'application/xml')

        request.META = {'HTTP_ACCEPT': 'application/json; charset=UTF-8'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        request.META = {'HTTP_ACCEPT': 'text/javascript,application/json'}
        self.assertEqual(determine_format(request, serializer), 'application/json')

        request.META = {'HTTP_ACCEPT': 'bogon'}
        self.assertRaises(BadRequest, determine_format, request, serializer)
