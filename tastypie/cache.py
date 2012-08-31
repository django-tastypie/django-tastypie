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
