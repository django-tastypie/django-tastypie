from urlparse import urlparse

from oauth.oauth import OAuthDataStore, OAuthError, escape

from django.conf import settings

from models import Nonce, Token, Consumer, Resource, generate_random
from consts import VERIFIER_SIZE, MAX_URL_LENGTH, OUT_OF_BAND

OAUTH_BLACKLISTED_HOSTNAMES = getattr(settings, 'OAUTH_BLACKLISTED_HOSTNAMES', [])

class DataStore(OAuthDataStore):
    """Layer between Python OAuth and Django database."""
    def __init__(self, oauth_request):
        self.signature = oauth_request.parameters.get('oauth_signature', None)
        self.timestamp = oauth_request.parameters.get('oauth_timestamp', None)
        self.scope = oauth_request.parameters.get('scope', 'all')

    def lookup_consumer(self, key):
        try:
            self.consumer = Consumer.objects.get(key=key)
            return self.consumer
        except Consumer.DoesNotExist:
            return None

    def lookup_token(self, token_type, token):
        if token_type == 'request':
            token_type = Token.REQUEST
        elif token_type == 'access':
            token_type = Token.ACCESS
        try:
            self.request_token = Token.objects.get(key=token, 
                                                   token_type=token_type)
            return self.request_token
        except Token.DoesNotExist:
            return None

    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        if oauth_token is None:
            return None
        nonce, created = Nonce.objects.get_or_create(consumer_key=oauth_consumer.key, 
                                                     token_key=oauth_token.key,
                                                     key=nonce)
        if created:
            return None
        else:
            return nonce.key

    def fetch_request_token(self, oauth_consumer, oauth_callback):
        if oauth_consumer.key != self.consumer.key:
            raise OAuthError('Consumer key does not match.')
        
        # OAuth 1.0a: if there is a callback, check its validity
        callback = None
        callback_confirmed = False
        if oauth_callback:
            if oauth_callback != OUT_OF_BAND:
                if check_valid_callback(oauth_callback):
                    callback = oauth_callback
                    callback_confirmed = True
                else:
                    raise OAuthError('Invalid callback URL.')

        try:
            resource = Resource.objects.get(name=self.scope)
        except:
            raise OAuthError('Resource %s does not exist.' % escape(self.scope))
        self.request_token = Token.objects.create_token(consumer=self.consumer,
                                                        token_type=Token.REQUEST,
                                                        timestamp=self.timestamp,
                                                        resource=resource,
                                                        callback=callback,
                                                        callback_confirmed=callback_confirmed)
        
        return self.request_token
        

    def fetch_access_token(self, oauth_consumer, oauth_token, oauth_verifier):
        if oauth_consumer.key == self.consumer.key \
        and oauth_token.key == self.request_token.key \
        and self.request_token.is_approved:
            # OAuth 1.0a: if there is a callback confirmed, check the verifier
            if (self.request_token.callback_confirmed \
            and oauth_verifier == self.request_token.verifier) \
            or not self.request_token.callback_confirmed:
                self.access_token = Token.objects.create_token(consumer=self.consumer,
                                                               token_type=Token.ACCESS,
                                                               timestamp=self.timestamp,
                                                               user=self.request_token.user,
                                                               resource=self.request_token.resource)
                return self.access_token
        raise OAuthError('Consumer key or token key does not match. ' \
                        +'Make sure your request token is approved. ' \
                        +'Check your verifier too if you use OAuth 1.0a.')

    def authorize_request_token(self, oauth_token, user):
        if oauth_token.key == self.request_token.key:
            # authorize the request token in the store
            self.request_token.is_approved = True
            
            # OAuth 1.0a: if there is a callback confirmed, we must set a verifier
            if self.request_token.callback_confirmed:
                self.request_token.verifier = generate_random(VERIFIER_SIZE)
            
            self.request_token.user = user
            self.request_token.save()
            return self.request_token
        raise OAuthError('Token key does not match.')


def check_valid_callback(callback):
    """
    Checks the size and nature of the callback.
    """
    callback_url = urlparse(callback)
    return (callback_url.scheme
            and callback_url.hostname not in OAUTH_BLACKLISTED_HOSTNAMES
            and len(callback) < MAX_URL_LENGTH)
