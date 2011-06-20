import json
import decimal
from django.contrib.auth.models import User
from django.test import TestCase
from core.tests.mocks import MockRequest
from django.conf import settings
from tastypie.serializers import Serializer
from inherited_models.api.resources import ProductResource
from inherited_models.api.urls import api
from inherited_models.models import Banana, Shirt, Product

settings.DEBUG = True


class ProductResourceTest(TestCase):
    urls = 'inherited_models.api.urls'

    def setUp(self):
        super(ProductResourceTest, self).setUp()
        self.banana1 = Banana.objects.create(price=decimal.Decimal('2.0'),
                                             weight=decimal.Decimal('0.200'))
        self.banana2 = Banana.objects.create(sick=True, price=decimal.Decimal('0.2'),
                                             weight=decimal.Decimal('0.220'))
        self.shirt1 = Shirt.objects.create(price=decimal.Decimal('15.0'),
                                           weight=decimal.Decimal('0.350'))

    def test_correct_relation(self):
        resource = api.canonical_resource_for('products')
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'
        resp = resource.wrap_view('dispatch_detail')(request, pk=self.banana1.pk)
        self.assertEqual(resp.status_code, 200)
        data = Serializer().deserialize(resp.content)
        self.assertEqual(decimal.Decimal(data['price']), decimal.Decimal('2.0'))
        self.assertEqual(decimal.Decimal(data['weight']), decimal.Decimal('0.200'))
