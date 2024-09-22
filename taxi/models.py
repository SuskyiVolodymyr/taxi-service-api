from django.db import models

from taxi_service import settings


class City(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "cities"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Driver(models.Model):
    SEX_CHOICES = {("M", "Male"), ("F", "Female")}
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    license_number = models.CharField(max_length=255)
    age = models.IntegerField()
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="drivers"
    )
    sex = models.CharField(max_length=6, choices=SEX_CHOICES)
    rate = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ["user__first_name"]

    def __str__(self) -> str:
        return self.user.full_name


class Car(models.Model):
    model = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="cars"
    )

    class Meta:
        ordering = ["model"]

    def __str__(self) -> str:
        return f"{self.driver}: {self.model}"


class DriverApplication(models.Model):
    SEX_CHOICES = {("M", "Male"), ("F", "Female")}
    STATUS_CHOICES = {("P", "Pending"), ("A", "Approved"), ("R", "Rejected")}
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    license_number = models.CharField(max_length=255)
    age = models.IntegerField()
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="applications"
    )
    sex = models.CharField(max_length=6, choices=SEX_CHOICES)
    status = models.CharField(
        max_length=6, choices=STATUS_CHOICES, default="P"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "created_at"]

    def __str__(self) -> str:
        return self.user.full_name


class Order(models.Model):

    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="orders"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    street_from = models.CharField(max_length=255)
    street_to = models.CharField(max_length=255)
    distance = models.IntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date_created"]

    def __str__(self) -> str:
        return f"{self.user}: {self.date_created}"


class Ride(models.Model):
    STATUS_CHOICES = {
        ("1", "Waiting for client"),
        ("2", "In process"),
        ("3", "Finished"),
    }
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name="rides"
    )
    status = models.CharField(
        max_length=6, choices=STATUS_CHOICES, default="1"
    )
    rate = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["status"]

    def __str__(self) -> str:
        return f"{self.driver}: {self.order}"
