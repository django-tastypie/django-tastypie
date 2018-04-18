from tastypie.resources import ModelResource

from ..models import User


class UserResource(ModelResource):
    class Meta:
        object_class = User.objects.all()
