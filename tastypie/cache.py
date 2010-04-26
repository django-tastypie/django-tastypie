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


class SimpleCache(NoCache):
    """
    Uses Django's current ``CACHE_BACKEND`` to store cached data.
    """
    def get(self, key):
        """
        Gets a key from the cache. Returns ``None`` if the key is not found.
        """
        return cache.get(key)
    
    def set(self, key, value, timeout=60):
        """
        Sets a key-value in the cache.
        
        Optionally accepts a ``timeout`` in seconds. Defaults to ``60`` seconds.
        """
        cache.set(key, value, timeout)
