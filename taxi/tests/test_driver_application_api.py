from unittest.mock import patch

from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from taxi.models import City, DriverApplication, Driver
from taxi.serializers import DriverApplicationListSerializer
from taxi.tests.base import TestBase

DRIVER_APPLICATION_URL = reverse("taxi:driverapplication-list")


def get_driver_application_detail(driver_application_id) -> str:
    return reverse(
        "taxi:driverapplication-detail", args=[driver_application_id]
    )


class UnauthorizedDriverApplicationAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.city = City.objects.create(name="test city")

    def sample_driver_application(self):
        return DriverApplication.objects.create(
            user=self.user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def test_unauthorized_user_cant_list_driver_applications(self):
        res = self.client.get(DRIVER_APPLICATION_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_create_driver_applications(self):
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_update_driver_applications(self):
        driver_application = self.sample_driver_application()

        payload = {
            "license_number": "654321",
            "age": 19,
            "city": self.city.id,
            "sex": "F",
        }
        res = self.client.patch(
            get_driver_application_detail(driver_application.id),
            payload,
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_delete_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.delete(
            get_driver_application_detail(driver_application.id)
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_reject_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.get(
            reverse(
                "taxi:driverapplication-reject", args=[driver_application.id]
            )
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_apply_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.get(
            reverse(
                "taxi:driverapplication-apply", args=[driver_application.id]
            )
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SimpleUserDriverApplicationAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.city = City.objects.create(name="test city")
        self.client.force_authenticate(user=self.user)
        self.user2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )

    def sample_driver_application(self, user: AUTH_USER_MODEL = None):
        if user is None:
            user = self.user
        return DriverApplication.objects.create(
            user=user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    @patch("taxi.serializers.send_message")
    def test_simple_user_can_create_driver_applications(
        self, mock_send_message
    ):
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        mock_send_message.assert_called_once()

    def test_simple_user_cant_create_driver_applications_with_active_application(
        self,
    ):
        self.sample_driver_application()
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_age_cant_be_less_than_18(self):
        payload = {
            "license_number": "123456",
            "age": 17,
            "city": self.city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_cant_create_application(self):
        self.user.is_driver = True
        self.user.save()
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_simple_user_cant_list_only_his_applications(self):
        driver_application = self.sample_driver_application()
        serializer1 = DriverApplicationListSerializer(driver_application)
        another_user_driver_application = self.sample_driver_application(
            self.user2
        )
        serializer2 = DriverApplicationListSerializer(
            another_user_driver_application
        )
        res = self.client.get(DRIVER_APPLICATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_simple_user_cant_update_driver_applications(self):
        driver_application = self.sample_driver_application()

        payload = {
            "license_number": "654321",
            "age": 19,
            "city": self.city.id,
            "sex": "F",
        }

        res = self.client.patch(
            get_driver_application_detail(driver_application.id),
            payload,
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_delete_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.delete(
            get_driver_application_detail(driver_application.id)
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_reject_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.get(
            reverse(
                "taxi:driverapplication-reject", args=[driver_application.id]
            )
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_apply_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.get(
            reverse(
                "taxi:driverapplication-apply", args=[driver_application.id]
            )
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminDriverApplicationAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin)
        self.city = City.objects.create(name="test city")

    def sample_driver_application(self):
        return DriverApplication.objects.create(
            user=self.user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def test_admin_can_list_all_applications(self):
        driver_application = self.sample_driver_application()
        serializer1 = DriverApplicationListSerializer(driver_application)
        res = self.client.get(DRIVER_APPLICATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)

    def test_admin_can_update_driver_applications(self):
        driver_application = self.sample_driver_application()

        payload = {
            "license_number": "654321",
            "age": 19,
            "city": self.city.id,
            "sex": "F",
        }

        res = self.client.patch(
            get_driver_application_detail(driver_application.id),
            payload,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_delete_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.delete(
            get_driver_application_detail(driver_application.id)
        )

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_reject_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.get(
            reverse(
                "taxi:driverapplication-reject", args=[driver_application.id]
            )
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_apply_driver_applications(self):
        driver_application = self.sample_driver_application()

        res = self.client.get(
            reverse(
                "taxi:driverapplication-apply", args=[driver_application.id]
            )
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_driver, True)

    def test_driver_created_after_application(self):
        driver_application = self.sample_driver_application()
        self.client.get(
            reverse(
                "taxi:driverapplication-apply", args=[driver_application.id]
            )
        )
        self.assertTrue(Driver.objects.filter(user=self.user).exists())
