from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from taxi.models import Driver, Car, City, DriverApplication


class TestBase(TestCase):
    def setUp(self):
        self.default_city = City.objects.create(name="test city")
        self.default_user = self.sample_user(
            email="default_user@test.com",
        )
        self.default_driver_user = self.sample_user(
            email="default_driver_user@test.com", is_driver=True
        )
        self.default_driver = self.sample_driver(self.default_driver_user)
        self.default_car = self.sample_car(self.default_driver)
        self.default_admin = self.sample_user(
            email="default_admin@admin.com",
            is_staff=True,
        )
        self.default_user_for_application = self.sample_user(
            email="default_user_for_application@test.com"
        )
        self.default_driver_application = self.sample_driver_application(
            self.default_user_for_application
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
            "is_staff": False,
        }
        payload.update(**params)
        return get_user_model().objects.create_user(**payload)

    def sample_driver_application(
        self, user: AUTH_USER_MODEL, **params
    ) -> DriverApplication:
        payload = {
            "user": user,
            "license_number": "123456",
            "age": 18,
            "city": self.default_city,
            "sex": "M",
            "status": "P",
        }
        payload.update(**params)
        return DriverApplication.objects.create(
            **payload,
        )
