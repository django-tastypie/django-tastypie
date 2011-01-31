from django.conf.urls.defaults import *

from views import request_token, user_authorization, access_token

urlpatterns = patterns('',
    url(r'^request_token/$',    request_token,      name='oauth_request_token'),
    url(r'^authorize/$',        user_authorization, name='oauth_user_authorization'),
    url(r'^access_token/$',     access_token,       name='oauth_access_token'),
)
