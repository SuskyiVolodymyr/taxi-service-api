from django.db import models

from taxi_service import settings


class City(models.Model):
    name = models.CharField(max_length=255)


class Driver(models.Model):
    SEX_CHOICES = {("M", "Male"), ("F", "Female")}
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    license_number = models.CharField(max_length=255)
    age = models.IntegerField()
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    sex = models.CharField(max_length=6, choices=SEX_CHOICES)
    rate = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )


class Car(models.Model):
    model = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    price_per_meter = models.DecimalField(max_digits=5, decimal_places=2)


class DriverApplication(models.Model):
    SEX_CHOICES = {("M", "Male"), ("F", "Female")}
    STATUS_CHOICES = {("P", "Pending"), ("A", "Approved"), ("R", "Rejected")}
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    license_number = models.CharField(max_length=255)
    age = models.IntegerField()
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    sex = models.CharField(max_length=6, choices=SEX_CHOICES)
    status = models.CharField(
        max_length=6, choices=STATUS_CHOICES, default="P"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
