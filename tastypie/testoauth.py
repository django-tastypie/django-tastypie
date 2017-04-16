#!/usr/bin/env python

import httplib2
import time,urlparse,urllib
import unittest
import oauth2 as oauth
import urllib2

CONSUMER_KEY = '123123123'
CONSUMER_SECRET = 'abcabcabc'

REQUEST_TOKEN_URL = 'http://localhost:8000/oauth/request_token/'
AUTHORIZE_URL = 'http://localhost:8000/oauth/authorize/?oauth_token='
ACCESS_TOKEN_URL = 'http://localhost:8000/oauth/access_token/'

parameters = {'oauth_consumer_key': CONSUMER_KEY,'oauth_signature_method': 'PLAINTEXT','oauth_signature': '%s&' %CONSUMER_SECRET,'oauth_timestamp': str(int(time.time())),'oauth_nonce': 'requestnonce','oauth_version': '1.0','oauth_callback': 'http://app.dev.shopety.com/oauth/authorize','scope': 'all',}
params = urllib.urlencode(parameters)

response=urllib2.urlopen(REQUEST_TOKEN_URL, params)
content = response.read()

print content
accessDict = dict(urlparse.parse_qsl(content))
print accessDict
request_token = accessDict['oauth_token']
request_token_secret = accessDict['oauth_token_secret']

print 'The request token for you is    ' + request_token 

print 'Please go to this url and authorize:   ' + AUTHORIZE_URL + request_token 

accepted = 'n'
while accepted.lower() == 'n':
  accepted = raw_input('Have you authorized me?()y/n')
oauth_verifier = raw_input('what is the verifier?    ')

parameters = {'oauth_consumer_key': CONSUMER_KEY,'oauth_token': request_token,'oauth_signature_method': 'PLAINTEXT','oauth_signature': '%s&%s' % (CONSUMER_SECRET, request_token_secret),'oauth_timestamp': str(int(time.time())),'oauth_nonce': 'accessnonce','oauth_version': '1.0','oauth_verifier': oauth_verifier,'scope': 'offer',}

params = urllib.urlencode(parameters)
response = urllib2.urlopen(ACCESS_TOKEN_URL,params)
content = response.read()
accessDict = dict(urlparse.parse_qsl(content))
access_token = accessDict['oauth_token']
access_token_secret = accessDict['oauth_token_secret']

print accessDict
print 'The access token for you is    ' + access_token 


