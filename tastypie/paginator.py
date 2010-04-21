from django.conf import settings
from tastypie.exceptions import BadRequest


class Paginator(object):
    def __init__(self, request_data, object_list, per_page=None, offset=0):
        self.request_data = request_data
        self.object_list = object_list
        self.per_page = per_page
        self.offset = offset
    
    def limit_per_page(self):
        limit = getattr(settings, 'API_LIMIT_PER_PAGE', 20)
        
        if 'limit' in self.request_data:
            limit = self.request_data['limit']
        elif self.per_page is not None:
            limit = self.per_page
        
        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer.")
        
        if limit < 0:
            raise BadRequest("Invalid limit '%s' provided. Please provide an integer >= 0.")
        
        return limit
    
    def starting_offset(self):
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
        return self.object_list[offset:offset + limit]
    
    def page(self):
        limit = self.limit_per_page()
        offset = self.starting_offset()
        objects = self.get_slice(limit, offset)
        return {
            'objects': objects,
            'offset': offset,
            'limit': limit,
        }
