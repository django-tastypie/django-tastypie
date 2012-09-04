from django.core.cache import cache


class NoCache(object):
    """
    A simplified, swappable base class for caching.

    Does nothing save for simulating the cache API.
    """
    def __init__(self, varies=None, *args, **kwargs):
        """
        Optionally accepts a ``varies`` list that will be used in the
        Vary header. Defaults to ["Accept"].
        """
        super(NoCache, self).__init__(*args, **kwargs)

        self.varies = varies if not varies is None else ["Accept"]

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

    def cacheable(self, request, response):
        """
        Returns True or False if the request -> response is capable of being
        cached.
        """
        return False

    def cache_control(self):
        """
        No-op for returning values for cache-control
        """
        pass


class SimpleCache(NoCache):
    """
    Uses Django's current ``CACHE_BACKEND`` to store cached data.
    """

    def __init__(self, timeout=60, *args, **kwargs):
        """
        Optionally accepts a ``timeout`` in seconds for the resource's cache.
        Defaults to ``60`` seconds.
        """
        super(SimpleCache, self).__init__(*args, **kwargs)

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

    def cacheable(self, request, response):
        """
        Returns True or False if the request -> response is capable of being
        cached.
        """
        return bool(request.method == "GET" and response.status_code == 200)

    def cache_control(self):
        control = dict(max_age=self.timeout, s_maxage=self.timeout)

        return control
