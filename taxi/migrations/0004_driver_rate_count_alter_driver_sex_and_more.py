# Generated by Django 5.0 on 2024-08-27 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taxi", "0003_alter_driver_sex_alter_driverapplication_sex_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="driver",
            name="rate_count",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="driver",
            name="sex",
            field=models.CharField(
                choices=[("M", "Male"), ("F", "Female")], max_length=6
            ),
        ),
        migrations.AlterField(
            model_name="driverapplication",
            name="sex",
            field=models.CharField(
                choices=[("M", "Male"), ("F", "Female")], max_length=6
            ),
        ),
        migrations.AlterField(
            model_name="ride",
            name="status",
            field=models.CharField(
                choices=[
                    ("3", "Finished"),
                    ("1", "Waiting for client"),
                    ("2", "In process"),
                ],
                default="1",
                max_length=6,
            ),
        ),
    ]
