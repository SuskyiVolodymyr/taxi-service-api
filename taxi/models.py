from django.db import models

from taxi_service import settings


class City(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.user.full_name


class Car(models.Model):
    model = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.driver}: {self.model}"


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

    def __str__(self):
        return self.user.full_name


class Order(models.Model):
    PAYMENT_STATUS_CHOICES = {
        ("1", "Pending"),
        ("2", "Paid"),
        ("3", "Cancelled"),
    }
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    street_from = models.CharField(max_length=255)
    street_to = models.CharField(max_length=255)
    distance = models.IntegerField()
    payment_status = models.CharField(
        max_length=6, choices=PAYMENT_STATUS_CHOICES, default="1"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user}: {self.date_created}"


class Ride(models.Model):
    STATUS_CHOICES = {
        ("1", "Waiting for client"),
        ("2", "In process"),
        ("3", "Finished"),
    }
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=6, choices=STATUS_CHOICES, default="1"
    )

    def __str__(self):
        return f"{self.driver}: {self.order}"
