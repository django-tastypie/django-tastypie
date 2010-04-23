from django.conf import settings
from django.core.urlresolvers import NoReverseMatch
from tastypie.exceptions import BadRequest
from urllib import urlencode


class Paginator(object):
    def __init__(self, request_data, objects, limit=None, offset=0):
        self.request_data = request_data
        self.objects = objects
        self.limit = limit
        self.offset = offset

        try:
            self.resource_uri = objects.get_resource_uri()
        except NoReverseMatch:
            self.resource_uri = None
    
    def get_limit(self):
        limit = getattr(settings, 'API_LIMIT_PER_PAGE', 20)
        
        if 'limit' in self.request_data:
            limit = self.request_data['limit']
        elif self.limit is not None:
            limit = self.limit
        
        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer.")
        
        if limit < 0:
            raise BadRequest("Invalid limit '%s' provided. Please provide an integer >= 0.")
        
        return limit
    
    def get_offset(self):
        offset = self.offset
        
        if 'offset' in self.request_data:
            offset = self.request_data['offset']
        
        try:
            offset = int(offset)
        except ValueError:
            raise BadRequest("Invalid offset '%s' provided. Please provide an integer.")
        
        if offset < 0:
            raise BadRequest("Invalid offset '%s' provided. Please provide an integer >= 0.")
        
        return offset
    
    def get_slice(self, limit, offset):
        return self.objects[offset:offset + limit]
    
    def get_count(self):
        return len(self.objects)

    def get_previous(self, limit, offset):
        if offset - limit < 0:
            return None
        return self._generate_uri(limit, offset-limit)

    def get_next(self, limit, offset, count):
        if offset + limit >= count:
            return None
        return self._generate_uri(limit, offset+limit)

    def _generate_uri(self, limit, offset):
        if self.resource_uri is None:
            return None
        return '%s?%s' % (self.resource_uri,
                          urlencode({'limit': limit, 'offset': offset}))

    def page(self):
        limit = self.get_limit()
        offset = self.get_offset()
        count = self.get_count()
        objects = self.get_slice(limit, offset)
        previous = self.get_previous(limit, offset)
        next = self.get_next(limit, offset, count)

        return {
            'objects': objects,
            'meta': {
                'offset': offset,
                'limit': limit,
                'total_count': count,
                'previous': previous,
                'next': next,
            }
        }
