from django.db import models


class Product(models.Model):
    price = models.DecimalField(decimal_places=2, max_digits=10)
    weight = models.DecimalField(decimal_places=2, max_digits=10)


class Shirt(Product):
    name = models.CharField(max_length=80)
    recommended = models.BooleanField(default=False)


class Banana(Product):
    sick = models.BooleanField(default=False)
