from django.core.cache import cache


class NoCache(object):
    """
    A simplified, swappable base class for caching.
    
    Does nothing save for simulating the cache API.
    """
    def get(self, key):
        """
        Always raises ``NotImplementedError`` for getting values in the cache.
        """
        raise NotImplementedError()

    def set(self, key, value, timeout=60):
        """
        Always raises ``NotImplementedError`` for setting values in the cache.
        """
        raise NotImplementedError()

    def delete(self, key):
        """
        Always raises ``NotImplementedError`` for deleting values in the cache.
        """
        raise NotImplementedError()

    def delete_many(self, keys):
        """
        If ``delete`` method raises ``NotImplementedError``, raises 
        ``NotImplementedError`` again. If not, the default behavior is 
        looping through all the key to delete the cache in keys  
        which is inefficiency.
        
        Note that this method is optional but highly recommended when 
        one implements the cache backend. 
        """
        try:
            for key in keys:
                self.delete(key)
        except NotImplementedError:
            raise NotImplementedError()
                           
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
        
