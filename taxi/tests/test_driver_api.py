from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from taxi.models import Driver, City
from taxi.tests.base import TestBase

DRIVER_URL = reverse("taxi:driver-list")


def get_driver_detail(driver_id) -> str:
    return reverse("taxi:driver-detail", args=[driver_id])


class TestAllowedMethods(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.admin)
        self.city = City.objects.create(name="test city")

    def sample_driver(self) -> Driver:
        return Driver.objects.create(
            user=self.user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def test_list_method_allowed(self):
        res = self.client.get(DRIVER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_method_allowed(self):
        driver = self.sample_driver()

        res = self.client.get(get_driver_detail(driver.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_method_not_allowed(self):
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.city.id,
            "sex": "M",
        }

        res = self.client.post(DRIVER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_method_not_allowed(self):
        driver = self.sample_driver()

        payload = {
            "license_number": "654321",
            "age": 19,
            "city": self.city.id,
            "sex": "F",
        }

        res = self.client.patch(
            get_driver_detail(driver.id),
            payload,
        )

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_method_not_allowed(self):
        driver = self.sample_driver()

        res = self.client.delete(get_driver_detail(driver.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UnauthorizedUserTest(TestBase):
    def setUp(self):
        super().setUp()
        self.city = City.objects.create(name="test city")

    def sample_driver(self) -> Driver:
        return Driver.objects.create(
            user=self.user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def test_unauthorized_user_can_list_driver(self):
        res = self.client.get(DRIVER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthorized_user_can_retrieve_driver(self):
        driver = self.sample_driver()

        res = self.client.get(get_driver_detail(driver.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)


class TestFirePermissions(TestBase):
    def setUp(self):
        super().setUp()
        self.city = City.objects.create(name="test city")

    def sample_driver(self) -> Driver:
        return Driver.objects.create(
            user=self.user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def test_unauthorized_user_cant_fire_driver(self):
        driver = self.sample_driver()

        res = self.client.get(
            reverse(
                "taxi:driver-fire",
                args=[driver.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_simple_user_cant_fire_driver(self):
        driver = self.sample_driver()
        user2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )
        self.client.force_authenticate(user=user2)

        res = self.client.get(
            reverse(
                "taxi:driver-fire",
                args=[driver.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_cant_fire_driver(self):
        driver = self.sample_driver()
        driver2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
            is_driver=True,
        )

        self.client.force_authenticate(user=driver2)

        res = self.client.get(
            reverse(
                "taxi:driver-fire",
                args=[driver.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_fire_driver(self):
        driver = self.sample_driver()

        self.client.force_authenticate(user=self.admin)

        res = self.client.get(
            reverse(
                "taxi:driver-fire",
                args=[driver.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Driver.objects.filter(id=driver.id).exists())
