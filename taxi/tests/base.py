from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from taxi.models import Driver, Car, City


class TestBase(TestCase):
    def setUp(self):
        self.default_city = City.objects.create(name="test city")
        self.default_user = get_user_model().objects.create_user(
            email="test@test.com",
            first_name="test",
            last_name="test",
            password="test1234",
        )
        self.default_driver_user = self.sample_user(
            email="driver_user@test.com", is_driver=True
        )
        self.default_driver = self.sample_driver(self.default_driver_user)
        self.default_car = self.sample_car(self.default_driver)
        self.default_admin = get_user_model().objects.create_superuser(
            email="admin@admin.com",
            first_name="admin",
            last_name="admin",
            password="admin1234",
        )

        self.client = APIClient()

    def sample_car(self, driver: Driver, **params) -> Car:
        payload = {
            "model": "test model",
            "number": "test number",
            "driver": driver,
        }
        payload.update(**params)
        return Car.objects.create(**payload)

    def sample_driver(self, user: AUTH_USER_MODEL, **params) -> Driver:
        payload = {
            "user": user,
            "license_number": "123456",
            "age": 18,
            "city": self.default_city,
            "sex": "M",
        }
        payload.update(**params)
        return Driver.objects.create(**payload)

    @staticmethod
    def sample_user(email: str, **params) -> AUTH_USER_MODEL:
        payload = {
            "email": email,
            "first_name": "test",
            "last_name": "test",
            "password": "test1234",
            "is_driver": False,
        }
        payload.update(**params)
        return get_user_model().objects.create_user(**payload)
