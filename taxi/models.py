from django.db import models


class Car(models.Model):
    model = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    driver = None
    price_per_meter = models.DecimalField(max_digits=5, decimal_places=2)
