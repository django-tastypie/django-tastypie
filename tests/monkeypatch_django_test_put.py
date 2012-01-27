
# MonkeyPatch so we can use PUT in Django 1.1, https://code.djangoproject.com/ticket/11371
        
import django.test.client
import urllib
from urlparse import urlparse

def put(self, path, data={}, content_type=django.test.client.MULTIPART_CONTENT,
        follow=False, **extra):
    """
    Send a resource to the server using PUT.
    """
    if content_type is django.test.client.MULTIPART_CONTENT:
        post_data = django.test.client.encode_multipart(django.test.client.BOUNDARY, data)
    else:
        post_data = data

    parsed = urlparse(path)
    r = {
        'CONTENT_LENGTH': len(post_data),
        'CONTENT_TYPE':   content_type,
        'PATH_INFO':      urllib.unquote(parsed[2]),
        'QUERY_STRING':   parsed[4],
        'REQUEST_METHOD': 'PUT',
        'wsgi.input':     django.test.client.FakePayload(post_data),
    }
    r.update(extra)

    response = self.request(**r)
    if follow:
        response = self._handle_redirects(response)
    return response

django.test.client.Client.put = put
