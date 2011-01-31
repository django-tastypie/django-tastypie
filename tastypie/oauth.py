from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from oauth_provider.models import *


class MyAuthentication(Authentication):
  def is_authenticated(self,request,**kwargs):
    if('access_token' not in request.GET):
      return False

    elif(request.GET['access_token'] != ''):
      a = request.GET['access_token']
      try:
        Token.objects.get(token_type=2, key = a)
        return True

      except:
        return False
