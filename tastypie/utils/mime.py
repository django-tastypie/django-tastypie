import mimeparse


def determine_format(request, serializer, default_format='application/json'):
    # First, check if they forced the format.
    if request.GET.get('format'):
        if request.GET['format'] in serializer.formats:
            return serializer.get_mime_for_format(request.GET['format'])

    # If callback parameter is present, use JSONP.
    if request.GET.has_key('callback'):
        return serializer.get_mime_for_format('jsonp')
    
    # Try to fallback on the Accepts header.
    if request.META.get('HTTP_ACCEPT', '*/*') != '*/*':
        best_format = mimeparse.best_match(serializer.supported_formats, request.META['HTTP_ACCEPT'])
        
        if best_format:
            return best_format
    
    # No valid 'Accept' header/formats. Sane default.
    return default_format


def build_content_type(format, encoding='utf-8'):
    if 'charset' in format:
        return format
    
    return "%s; charset=%s" % (format, encoding)
