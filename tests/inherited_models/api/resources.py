from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from inherited_models.models import Shirt, Product, Banana


class ShirtResource(ModelResource):
    class Meta:
        resource_name = 'shirts'
        queryset = Shirt.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()


class BananaResource(ModelResource):
    class Meta:
        resource_name = 'bananas'
        queryset = Banana.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()


class ProductResource(ModelResource):
    shirts = fields.ToManyField(ShirtResource, 'shirt', full=True, null=True)
    bananas = fields.ToManyField(BananaResource, 'banana', full=True, null=True)

    class Meta:
        queryset = Product.objects.all()
        resource_name = 'products'
        authorization = Authorization()
