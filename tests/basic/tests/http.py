from tests.testcases import TestServerTestCase
import httplib

class HTTPTestCase(TestServerTestCase):
    def setUp(self):
        self.start_test_server(address='localhost', port=8001)

    def tearDown(self):
        self.stop_test_server()

    def test_get_apis(self):
        connection = httplib.HTTPConnection('localhost', 8001)
        connection.request('GET', '/api/v1/')
        response = connection.getresponse()
        data = response.read()
        self.assertEqual(data, '{"notes": "/api/v1/notes/"}')
