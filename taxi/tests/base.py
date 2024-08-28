from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class TestBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            first_name="test",
            last_name="test",
            password="test1234",
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@admin.com",
            first_name="admin",
            last_name="admin",
            password="admin1234",
        )

        self.client = APIClient()
