import mimeparse
import re


def determine_format(request, serializer, default_format='application/json'):
    """
    Tries to "smartly" determine which output format is desired.
    
    First attempts to find a ``format`` override from the request and supplies
    that if found.
    
    If no request format was demanded, it falls back to ``mimeparse`` and the
    ``Accepts`` header, allowing specification that way.
    
    If still no format is found, returns the ``default_format`` (which defaults
    to ``application/json`` if not provided).
    """
    # First, check if they forced the format.
    if request.GET.get('format'):
        if request.GET['format'] in serializer.formats:
            return serializer.get_mime_for_format(request.GET['format'])
    
    # If callback parameter is present, use JSONP.
    if request.GET.has_key('callback'):
        return serializer.get_mime_for_format('jsonp')
    
    # Try to fallback on the Accepts header.
    if request.META.get('HTTP_ACCEPT', '*/*') != '*/*':
        formats = list(serializer.supported_formats) or []
        # Reverse the list, because mimeparse is weird like that. See also
        # https://github.com/toastdriven/django-tastypie/issues#issue/12 for
        # more information.
        formats.reverse()
        best_format = mimeparse.best_match(formats, request.META['HTTP_ACCEPT'])
        
        if best_format:
            return best_format
    
    # No valid 'Accept' header/formats. Sane default.
    return default_format


def build_content_type(format, encoding='utf-8', api=None):
    """
    Adds the vnd.api.<api_name> attribute to the content type
    (if using AcceptHeaderRouter) and appends the character encoding.
    """
    if api and api._accept_header_routing:
        type, subtype, vars = mimeparse.parse_mime_type(format)
        subtype = 'vnd.api.%s+%s' % (api.api_name, subtype)
        attributes = ''
        for k, v in vars.iteritems():
            attributes += '; %s=%s' % (k, v)
        format = '%s/%s%s' % (type, subtype, attributes)
    if 'charset' in format:
        return format
    
    return "%s; charset=%s" % (format, encoding)

# Anything surrounded by pluses and vnd.api.<apiname>
# will be removed.
_unwrap_match = re.compile('\+?vnd\.api\.[^\+;]+\+?')


def unwrap_content_type(format):
    """
    Removes the api name from the provided ``format``, if present.
    """
    return _unwrap_match.sub('', format)
