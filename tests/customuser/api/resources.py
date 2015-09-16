from tastypie.authorization import Authorization
from tastypie.resources import ModelResource

from customuser.models import CustomUser


class CustomUserResource(ModelResource):
    class Meta:
        queryset = CustomUser.objects.all()
        resource_name = 'customusers'
        authorization = Authorization()
