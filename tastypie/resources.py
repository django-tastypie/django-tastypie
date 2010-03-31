import mimeparse
from django.conf.urls.defaults import patterns, url
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404, HttpResponse, HttpResponseRedirect
from tastypie.http import HttpCreated, HttpAccepted, HttpSeeOther, HttpNotModified, HttpConflict, HttpGone, HttpMethodNotAllowed, HttpNotImplemented
from tastypie.serializers import Serializer


class Resource(object):
    """
    Mostly for dispatch and responding to requests.
    
    The business logic of what data is available is covered by the
    ``Representation`` object.
    
    Serialization/deserialization is handled "at the edges" (i.e. at the
    beginning/end of the request/response cycle) so that everything internally
    is Python data structures.
    """
    representation = None
    list_representation = None
    detail_representation = None
    serializer = Serializer()
    allowed_methods = None
    list_allowed_methods = ['get', 'post', 'put', 'delete']
    detail_allowed_methods = ['get', 'post', 'put', 'delete']
    per_page = 20
    url_prefix = None
    default_format = 'text/html'
    
    def __init__(self, representation=None, list_representation=None,
                 detail_representation=None, serializer=None,
                 allowed_methods=None, list_allowed_methods=None,
                 detail_allowed_methods=None, per_page=None, url_prefix=None):
        # Shortcut to specify both via arguments.
        if representation is not None:
            self.representation = representation
        
        # Shortcut to specify both at the class level.
        if self.representation is not None:
            self.list_representation = self.representation
            self.detail_representation = self.representation
        
        if list_representation is not None:
            self.list_representation = list_representation
        
        if detail_representation is not None:
            self.detail_representation = detail_representation
        
        if serializer is not None:
            self.serializer = serializer
        
        # Shortcut to specify both via arguments.
        if allowed_methods is not None:
            self.allowed_methods = allowed_methods
        
        # Shortcut to specify both at the class level.
        if self.allowed_methods is not None:
            self.list_allowed_methods = self.allowed_methods
            self.detail_allowed_methods = self.allowed_methods
        
        if list_allowed_methods is not None:
            self.list_allowed_methods = list_allowed_methods
        
        if detail_allowed_methods is not None:
            self.detail_allowed_methods = detail_allowed_methods
        
        if per_page is not None:
            self.per_page = per_page
        
        if url_prefix is not None:
            self.url_prefix = url_prefix
        
        # Make sure we're good to go.
        if self.list_representation is None:
            raise ImproperlyConfigured("No general representation or specific list representation provided.")
        
        if self.detail_representation is None:
            raise ImproperlyConfigured("No general representation or specific detail representation provided.")
        
        if self.serializer is None:
            raise ImproperlyConfigured("No serializer provided.")
        
        if not self.url_prefix:
            raise ImproperlyConfigured("No url_prefix provided.")
    
    def wrap_view(self, view):
        def wrap(view):
            def wrapper(request, *args, **kwargs):
                return getattr(self, view)(request, *args, **kwargs)
            return wrapper
        return wrap
    
    @property
    def urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.wrap_view(self.dispatch_list), name='api_%s_dispatch_list' % self.url_prefix),
            url(r'^(?P<obj_id>\d+)/$', self.wrap_view(self.dispatch_detail), name='api_%s_dispatch_detail' % self.url_prefix),
        )
        return urlpatterns
    
    # FIXME:
    #   - Barkeeper's Friend links?
    
    def determine_format(self, request):
        # First, check if they forced the format.
        if request.GET.get('format'):
            if request.GET['format'] in self.serializer.formats:
                return self.serializer.get_mime_for_format(request.GET['format'])
        
        # Try to fallback on the Accepts header.
        if request.META.get('HTTP_ACCEPT'):
            best_format = mimeparse.best_match(self.serializer.supported_formats, request.META['HTTP_ACCEPT'])
            
            if best_format:
                return best_format
        
        # No valid 'Accept' header/formats. Sane default.
        return self.default_format
    
    def dispatch_list(self, request, format=None):
        request_method = request.method.lower()
        
        if not request_method in self.list_allowed_methods:
            return HttpMethodNotAllowed
        
        method = getattr(self, "%s_list" % request_method, None)
        
        if method is None:
            return HttpNotImplemented
        
        request = convert_post_to_put(request)
        response = method(request)
        
        if not isinstance(response, HttpResponse):
            return HttpAccepted()
        
        return response
    
    def dispatch_detail(self, request, *args):
        request_method = request.method.lower()
        
        if not request_method in self.detail_allowed_methods:
            return HttpMethodNotAllowed
        
        method = getattr(self, "%s_detail" % request_method, None)
        
        if method is None:
            return HttpNotImplemented
        
        request = convert_post_to_put(request)
        response = method(request)
        
        if not isinstance(response, HttpResponse):
            return HttpAccepted()
        
        return response
    
    def get_list(self, request):
        """
        Should return a HttpResponse (200 OK).
        """
        # FIXME: Pagination (likely manually due to individual reps. Generator?)
        results = (self.representation.read(obj) for obj in self.representation.get_list())[:self.per_page]
        
        serialized, content_type = self.serialize(results)
        # FIXME: Include charset here.
        return HttpResponse(content=serialized, content_type=content_type)
    
    def get_detail(self, request, obj_id):
        """
        Should return a HttpResponse (200 OK).
        """
        try:
            obj = self.representation.get(obj_id)
        except:
            return HttpGone()
        
        serialized, content_type = self.serialize(self.representation.read(obj))
        # FIXME: Include charset here.
        return HttpResponse(content=serialized, content_type=content_type)
    
    def put_list(self, request):
        """
        Replaces a collection of resources with another collection.
        Return ``HttpAccepted`` (204 No Content).
        """
        # self.representation.delete()
        # self.representation.update()
        # return HttpAccepted()
        raise NotImplementedError
    
    def put_detail(self, request, obj_id):
        """
        If a new resource is created, return ``HttpCreated`` (201 Created).
        If an existing resource is modified, return ``HttpAccepted`` (204 No Content).
        """
        # FIXME: Forced for now but needs content-type detection and error-handling.
        deserialized = self.serializer.from_json(request.raw_post_data)
        representation = self.representation()
        
        try:
            resource = representation.update(pk=obj_id, data_dict=deserialized)
            return HttpAccepted()
        except:
            resource = representation.create(data_dict=deserialized)
            # FIXME: Include charset here.
            return HttpCreated(location=resource.get_resource_uri())
    
    def post_list(self, request):
        """
        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        # TODO: What to do if the resource already exists at that id? Quietly
        #       update or complain loudly?
        # FIXME: Forced for now but needs content-type detection and error-handling.
        deserialized = self.serializer.from_json(request.raw_post_data)
        representation = self.representation()
        resource = self.representation.create(deserialized)
        return HttpCreated(location=resource.get_resource_uri())
    
    def post_detail(self, request, obj_id):
        """
        This is not implemented by default because most people's data models
        aren't self-referential.
        
        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        raise NotImplementedError
    
    def delete_list(self, request):
        """
        If the resources are deleted, return ``HttpAccepted`` (204 No Content).
        """
        # TODO: What range ought to be deleted? This seems particularly
        #       dangerous.
        representation = self.representation()
        representation.queryset.all().delete()
        return HttpAccepted()
    
    def delete_detail(self, request, obj_id):
        """
        If the resource is deleted, return ``HttpAccepted`` (204 No Content).
        """
        representation = self.representation()
        
        try:
            representation.delete(pk=obj_id)
            return HttpAccepted()
        except:
            return HttpGone()


# Based off of ``piston.utils.coerce_put_post``. Similarly BSD-licensed.
# And no, the irony is not lost on me.
def convert_post_to_put(request):
    """
    Force Django to process the PUT.
    """
    if request.method == "PUT":
        if hasattr(request, '_post'):
            del request._post
            del request._files
        
        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = "PUT"
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'
            
        request.PUT = request.POST
    
    return request
