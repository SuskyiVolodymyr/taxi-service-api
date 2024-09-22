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
    def test_unauthorized_user_cant_list_driver_applications(self):
        res = self.client.get(DRIVER_APPLICATION_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_create_driver_applications(self):
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.default_city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_update_driver_applications(self):
        payload = {
            "license_number": "654321",
            "age": 19,
            "city": self.default_city.id,
            "sex": "F",
        }
        res = self.client.patch(
            get_driver_application_detail(self.default_driver_application.id),
            payload,
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_delete_driver_applications(self):
        res = self.client.delete(
            get_driver_application_detail(self.default_driver_application.id)
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_reject_driver_applications(self):
        res = self.client.get(
            reverse(
                "taxi:driverapplication-reject",
                args=[self.default_driver_application.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_apply_driver_applications(self):
        res = self.client.get(
            reverse(
                "taxi:driverapplication-apply",
                args=[self.default_driver_application.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SimpleUserDriverApplicationAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_user)

    @patch("taxi.serializers.send_message")
    def test_simple_user_can_create_driver_applications(
        self, mock_send_message
    ):
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.default_city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        mock_send_message.assert_called_once()

    def test_simple_user_cant_create_driver_applications_with_active_application(
        self,
    ):
        self.sample_driver_application(self.default_user)
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.default_city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_age_cant_be_less_than_18(self):
        payload = {
            "license_number": "123456",
            "age": 17,
            "city": self.default_city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_cant_create_application(self):
        self.client.force_authenticate(user=self.default_driver_user)
        payload = {
            "license_number": "123456",
            "age": 18,
            "city": self.default_city.id,
            "sex": "M",
        }
        res = self.client.post(DRIVER_APPLICATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_simple_user_cant_list_only_his_applications(self):
        driver_application = self.sample_driver_application(self.default_user)
        serializer1 = DriverApplicationListSerializer(driver_application)
        serializer2 = DriverApplicationListSerializer(
            self.default_driver_application
        )
        res = self.client.get(DRIVER_APPLICATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_simple_user_cant_update_driver_applications(self):
        driver_application = self.sample_driver_application(self.default_user)
        payload = {
            "license_number": "654321",
            "age": 19,
            "city": self.default_city.id,
            "sex": "F",
        }

        res = self.client.patch(
            get_driver_application_detail(driver_application.id),
            payload,
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_delete_driver_applications(self):
        driver_application = self.sample_driver_application(self.default_user)

        res = self.client.delete(
            get_driver_application_detail(driver_application.id)
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_reject_driver_applications(self):
        driver_application = self.sample_driver_application(self.default_user)

        res = self.client.get(
            reverse(
                "taxi:driverapplication-reject", args=[driver_application.id]
            )
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_apply_driver_applications(self):
        driver_application = self.sample_driver_application(self.default_user)

        res = self.client.get(
            reverse(
                "taxi:driverapplication-apply", args=[driver_application.id]
            )
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminDriverApplicationAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_admin)

    def test_admin_can_list_all_applications(self):
        serializer1 = DriverApplicationListSerializer(
            self.default_driver_application
        )
        res = self.client.get(DRIVER_APPLICATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)

    def test_filter_by_status(self):
        driver_application2 = self.sample_driver_application(
            self.default_user, status="R"
        )

        serializer1 = DriverApplicationListSerializer(
            self.default_driver_application
        )
        serializer2 = DriverApplicationListSerializer(driver_application2)

        res = self.client.get(DRIVER_APPLICATION_URL, {"status": "P"})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_admin_can_update_driver_applications(self):
        payload = {
            "license_number": "654321",
            "age": 19,
            "city": self.default_city.id,
            "sex": "F",
        }

        res = self.client.patch(
            get_driver_application_detail(self.default_driver_application.id),
            payload,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_delete_driver_applications(self):
        res = self.client.delete(
            get_driver_application_detail(self.default_driver_application.id)
        )

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_reject_driver_applications(self):
        res = self.client.get(
            reverse(
                "taxi:driverapplication-reject",
                args=[self.default_driver_application.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_apply_driver_applications(self):
        res = self.client.get(
            reverse(
                "taxi:driverapplication-apply",
                args=[self.default_driver_application.id],
            )
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.default_user_for_application.refresh_from_db()
        self.assertEqual(self.default_user_for_application.is_driver, True)

    def test_driver_created_after_application(self):
        self.client.get(
            reverse(
                "taxi:driverapplication-apply",
                args=[self.default_driver_application.id],
            )
        )
        self.assertTrue(
            Driver.objects.filter(
                user=self.default_user_for_application
            ).exists()
        )
