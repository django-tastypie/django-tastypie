import time
from django.core.cache import cache


class BaseThrottle(object):
    def __init__(self, throttle_at=150, timeframe=3600, expiration=None):
        self.throttle_at = throttle_at
        # In seconds, please.
        self.timeframe = timeframe
        
        if expiration is None:
            # Expire in a week.
            expiration = 60 * 60 * 24 * 7
        
        self.expiration = int(expiration)
    
    def convert_identifier_to_key(self, identifier):
        bits = []
        
        for char in identifier:
            if char.isalnum() or char in ['_', '.', '-']:
                bits.append(char)
        
        safe_string = ''.join(bits)
        return "%s_accesses" % safe_string
    
    def should_be_throttled(self, identifier, **kwargs):
        return False
    
    def accessed(self, identifier, **kwargs):
        pass


class CacheThrottle(BaseThrottle):
    def should_be_throttled(self, identifier, **kwargs):
        key = self.convert_identifier_to_key(identifier)
        
        # Make sure something is there.
        cache.add(key, [])
        
        # Weed out anything older than the timeframe.
        minimum_time = int(time.time()) - int(self.timeframe)
        times_accessed = [access for access in cache.get(key) if access >= minimum_time]
        cache.set(key, times_accessed, self.expiration)
        
        if len(times_accessed) >= int(self.throttle_at):
            # Throttle them.
            return True
        
        # Let them through.
        return False
    
    def accessed(self, identifier, **kwargs):
        key = self.convert_identifier_to_key(identifier)
        times_accessed = cache.get(key, [])
        times_accessed.append(int(time.time()))
        cache.set(key, times_accessed, self.expiration)


class CacheDBThrottle(CacheThrottle):
    def accessed(self, identifier, **kwargs):
        # Do the import here, instead of top-level, so that the model is
        # only required when using this throttling mechanism.
        from tastypie.models import ApiAccess
        super(CacheDBThrottle, self).accessed(identifier, **kwargs)
        # Write out the access to the DB for logging purposes.
        ApiAccess.objects.create(
            identifier=identifier,
            url=kwargs.get('url', ''),
            request_method=kwargs.get('request_method', '')
        )
