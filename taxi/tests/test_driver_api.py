from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from taxi.models import Driver, City
from taxi.serializers import DriverListSerializer
from taxi.tests.base import TestBase

DRIVER_URL = reverse("taxi:driver-list")


def get_driver_detail(driver_id) -> str:
    return reverse("taxi:driver-detail", args=[driver_id])


class TestAllowedMethods(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.default_admin)

    def test_list_method_allowed(self):
        res = self.client.get(DRIVER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_method_allowed(self):
        res = self.client.get(get_driver_detail(self.default_driver.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_method_not_allowed(self):
        res = self.client.post(DRIVER_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_method_not_allowed(self):
        res = self.client.patch(get_driver_detail(self.default_driver.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_method_not_allowed(self):
        res = self.client.delete(get_driver_detail(self.default_driver.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UnauthorizedUserTest(TestBase):

    def test_unauthorized_user_can_list_driver(self):
        res = self.client.get(DRIVER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthorized_user_can_retrieve_driver(self):
        res = self.client.get(get_driver_detail(self.default_driver.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)


class TestFirePermissions(TestBase):
    def setUp(self):
        super().setUp()

    def test_unauthorized_user_cant_fire_driver(self):
        res = self.client.get(
            reverse(
                "taxi:driver-fire",
                args=[self.default_driver.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_simple_user_cant_fire_driver(self):
        self.client.force_authenticate(user=self.default_user)

        res = self.client.get(
            reverse(
                "taxi:driver-fire",
                args=[self.default_driver.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_cant_fire_driver(self):
        driver_user_2 = self.sample_user(
            email="test2@test.com",
            is_driver=True,
        )
        driver_2 = self.sample_driver(driver_user_2)

        self.client.force_authenticate(user=self.default_driver_user)

        res = self.client.get(
            reverse(
                "taxi:driver-fire",
                args=[driver_2.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_fire_driver(self):
        self.client.force_authenticate(user=self.default_admin)

        res = self.client.get(
            reverse(
                "taxi:driver-fire",
                args=[self.default_driver.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Driver.objects.filter(id=self.default_driver.id).exists()
        )


class TestFiltering(TestBase):

    def test_filter_by_first_name(self):
        user2 = self.sample_user(
            email="test2@test.com",
            first_name="Robert",
            is_driver=True,
        )
        driver2 = self.sample_driver(user2)

        serializer1 = DriverListSerializer(self.default_driver)
        serializer2 = DriverListSerializer(driver2)

        res = self.client.get(DRIVER_URL, {"first_name": "ro"})

        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer1.data, res.data)

    def test_filter_by_last_name(self):
        user2 = self.sample_user(
            email="test2@test.com",
            last_name="Smith",
            is_driver=True,
        )
        driver2 = self.sample_driver(user2)

        serializer1 = DriverListSerializer(self.default_driver)
        serializer2 = DriverListSerializer(driver2)

        res = self.client.get(DRIVER_URL, {"last_name": "sm"})

        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer1.data, res.data)

    def test_filter_by_city(self):
        user2 = self.sample_user(
            email="test2@test.com",
            is_driver=True,
        )
        new_city = City.objects.create(name="test city 2")
        driver2 = self.sample_driver(user2, city=new_city)

        serializer1 = DriverListSerializer(self.default_driver)
        serializer2 = DriverListSerializer(driver2)

        res = self.client.get(DRIVER_URL, {"city": "2"})

        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer1.data, res.data)
