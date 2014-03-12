import socket
import threading

from django.core.handlers.wsgi import WSGIHandler
from django.core.management import call_command
from django.core.servers import basehttp
from django.db import connections
from django.test.testcases import TransactionTestCase

class StoppableWSGIServer(basehttp.WSGIServer):
    """WSGIServer with short timeout, so that server thread can stop this server."""

    def server_bind(self):
        """Sets timeout to 1 second."""
        basehttp.WSGIServer.server_bind(self)
        self.socket.settimeout(1)

    def get_request(self):
        """Checks for timeout when getting request."""
        try:
            sock, address = self.socket.accept()
            sock.settimeout(None)
            return (sock, address)
        except socket.timeout:
            raise

class TestServerThread(threading.Thread):
    """Thread for running a http server while tests are running."""

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self._stopevent = threading.Event()
        self.started = threading.Event()
        self.error = None
        super(TestServerThread, self).__init__()

    def run(self):
        """Sets up test server and database and loops over handling http requests."""
        try:
            handler = WSGIHandler()
            server_address = (self.address, self.port)
            httpd = StoppableWSGIServer(server_address, basehttp.WSGIRequestHandler)
            httpd.set_app(handler)
            self.started.set()
        except basehttp.WSGIServerException as e:
            self.error = e
            self.started.set()
            return

        # Must do database stuff in this new thread if database in memory.
        from django.conf import settings
        
        db = settings.DATABASES['default']
        
        ENGINE = db['ENGINE']
        TEST_NAME = db.get('TEST_NAME')
        
        if ('sqlite3' in ENGINE or 'spatialite' in ENGINE) \
            and (not TEST_NAME or TEST_NAME == ':memory:'):
            if 'spatialite' in ENGINE:
                cursor = connections['default'].cursor()
                
                cursor.execute('SELECT InitSpatialMetaData()')
                row = cursor.fetchone()
            
            call_command('syncdb', interactive=False, verbosity=0)
            
            # Import the fixture data into the test database.
            if hasattr(self, 'fixtures'):
                # We have to use this slightly awkward syntax due to the fact
                # that we're using *args and **kwargs together.
                call_command('loaddata', *self.fixtures, **{'verbosity': 0})

        # Loop until we get a stop event.
        while not self._stopevent.isSet():
            httpd.handle_request()

    def join(self, timeout=None):
        """Stop the thread and wait for it to finish."""
        self._stopevent.set()
        threading.Thread.join(self, timeout)


class TestServerTestCase(TransactionTestCase):
    def start_test_server(self, address='localhost', port=8000):
        """Creates a live test server object (instance of WSGIServer)."""
        self.server_thread = TestServerThread(address, port)
        self.server_thread.start()
        self.server_thread.started.wait()
        if self.server_thread.error:
            raise self.server_thread.error

    def stop_test_server(self):
        if self.server_thread:
            self.server_thread.join()
