from django.db import models

from user.models import Driver


class City(models.Model):
    name = models.CharField(max_length=255)


class Car(models.Model):
    model = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    price_per_meter = models.DecimalField(max_digits=5, decimal_places=2)
