# Generated by Django 5.0 on 2024-08-24 10:15

import django_enum.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    django_enum.fields.EnumCharField(
                        choices=[
                            ("1", "Pending"),
                            ("2", "Paid"),
                            ("3", "Canceled"),
                        ],
                        max_length=1,
                    ),
                ),
                ("session_url", models.URLField(max_length=500)),
                ("session_id", models.CharField(max_length=100)),
                (
                    "money_to_pay",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
            ],
        ),
    ]
