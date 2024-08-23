# Generated by Django 5.0 on 2024-08-23 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taxi", "0008_alter_driver_sex_alter_driverapplication_sex_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="driverapplication",
            name="status",
            field=models.CharField(
                choices=[
                    ("A", "Approved"),
                    ("P", "Pending"),
                    ("R", "Rejected"),
                ],
                default="P",
                max_length=6,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="payment_status",
            field=models.CharField(
                choices=[("2", "Paid"), ("3", "Cancelled"), ("1", "Pending")],
                default="1",
                max_length=6,
            ),
        ),
    ]
