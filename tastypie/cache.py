from django.core.cache import cache


class NoCache(object):
    def get(self, key):
        return None
    
    def set(self, key, value, timeout=60):
        pass


class SimpleCache(NoCache):
    def get(self, key):
        return cache.get(key)
    
    def set(self, key, value, timeout=60):
        cache.set(key, value, timeout)
