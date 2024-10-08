from django.db import models
from django_enum import EnumField

from taxi.models import Order


class Payment(models.Model):
    class StatusEnum(models.TextChoices):
        pending = "1", "Pending"
        paid = "2", "Paid"
        canceled = "3", "Canceled"

    status = EnumField(StatusEnum)
    session_url = models.URLField(max_length=500, null=True, blank=True)
    session_id = models.CharField(max_length=100)
    money_to_pay = models.DecimalField(decimal_places=2, max_digits=10)
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )

    class Meta:
        ordering = ["status"]
