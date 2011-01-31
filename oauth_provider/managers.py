from django.db import models
from django.contrib.auth.models import User

from consts import KEY_SIZE, SECRET_SIZE

class ConsumerManager(models.Manager):
    def create_consumer(self, name, user=None):
        """Shortcut to create a consumer with random key/secret."""
        consumer, created = self.get_or_create(name=name)
        if user is not None:
            consumer.user = user
        if created:
            consumer.generate_random_codes()
        return consumer
    
    _default_consumer = None
    def get_default_consumer(self, name):
        """Add cache if you use a default consumer."""
        if self._default_consumer is None:
            self._default_consumer = self.get(name=name)
        return self._default_consumer
        

class ResourceManager(models.Manager):
    _default_resource = None
    def get_default_resource(self, name):
        """Add cache if you use a default resource."""
        if self._default_resource is None:
            self._default_resource = self.get(name=name)
        return self._default_resource
        

class TokenManager(models.Manager):
    def create_token(self, consumer, token_type, timestamp, resource, 
            user=None, callback=None, callback_confirmed=False):
        """Shortcut to create a token with random key/secret."""
        token, created = self.get_or_create(consumer=consumer, 
                                            token_type=token_type, 
                                            timestamp=timestamp,
                                            resource=resource,
                                            user=user,
                                            callback=callback,
                                            callback_confirmed=callback_confirmed)
        if created:
            token.generate_random_codes()
        return token
