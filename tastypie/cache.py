from django.core.cache import cache


class NoCache(object):
    """
    A simplified, swappable base class for caching.
    
    Does nothing save for simulating the cache API.
    """
    def get(self, key):
        """
        Always returns ``None``.
        """
        return None

    def set(self, key, value, timeout=60):
        """
        No-op for setting values in the cache.
        """
        pass

    def delete(self, key):
        """
        No-op for deleting values in the cache.
        """
        pass

    def delete_many(self, keys):
        """
        No-op for deleting a bunch of keys when the class type is NoCache.  
        Note that this method is optional but highly recommended when 
        implementing the cache backend. If this method is not implemented 
        by user, the default behavior is looping through all the key in keys 
        which is inefficiency.
        """
        for key in keys:
            self.delete(key)
                       
class SimpleCache(NoCache):
    """
    Uses Django's current ``CACHE_BACKEND`` to store cached data.
    """

    def __init__(self, timeout=60):
        """
        Optionally accepts a ``timeout`` in seconds for the resource's cache.
        Defaults to ``60`` seconds.
        """
        self.timeout = timeout

    def get(self, key):
        """
        Gets a key from the cache. Returns ``None`` if the key is not found.
        """
        return cache.get(key)

    def set(self, key, value, timeout=None):
        """
        Sets a key-value in the cache.

        Optionally accepts a ``timeout`` in seconds. Defaults to ``None`` which
        uses the resource's default timeout.
        """
        if timeout == None:
            timeout = self.timeout

        cache.set(key, value, timeout)

    def delete(self, key):
        """
        Deletes a key-value in the cache.
        """
        cache.delete(key)
        
    def delete_many(self, keys):
        """
        Deletes a bunch of keys at once in the cache.
        """
        cache.delete_many(keys)
        
