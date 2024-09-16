from unittest.mock import patch

from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from taxi.models import Order, City, Driver, Car, Ride
from taxi.serializers import RideListSerializer
from taxi.tests.base import TestBase


RIDE_URL = reverse("taxi:ride-list")


def get_ride_detail(ride_id) -> str:
    return reverse("taxi:ride-detail", args=[ride_id])


class TestAllowedMethods(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.default_admin)

    def test_create_method_not_allowed(self):
        order = self.sample_order(self.default_user)

        payload = {
            "order": order.id,
            "driver": self.default_driver.id,
            "car": self.default_car.id,
        }

        res = self.client.post(RIDE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_method_not_allowed(self):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        payload = {
            "order": order.id,
            "driver": self.default_driver.id,
            "car": self.default_car.id,
        }

        res = self.client.patch(get_ride_detail(ride.id), payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UnauthorizedRideAPITest(TestBase):
    def test_unauthorized_cant_list_rides(self):
        res = self.client.get(RIDE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_cant_delete_rides(self):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.delete(get_ride_detail(ride.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_cant_change_rides_status_to_in_process(self):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.get(reverse("taxi:ride-in-process", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("taxi.views.send_message")
    def test_unauthorized_cant_change_rides_status_to_finished(
        self, mock_send_message
    ):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.get(reverse("taxi:ride-finished", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_send_message.assert_not_called()


class SimpleUserRideAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.default_user)

    def test_simple_user_can_list_rides(self):
        res = self.client.get(RIDE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_simple_user_can_list_only_his_rides(self):
        order1 = self.sample_order(self.default_user)
        another_user = self.sample_user("another_user@example.com")
        order2 = self.sample_order(another_user)
        ride1 = Ride.objects.create(
            order=order1,
            driver=self.default_driver,
            car=self.default_car,
        )

        ride2 = Ride.objects.create(
            order=order2,
            driver=self.default_driver,
            car=self.default_car,
        )

        serializer1 = RideListSerializer(ride1)
        serializer2 = RideListSerializer(ride2)

        res = self.client.get(RIDE_URL)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_simple_user_cant_delete_rides(self):
        order = self.sample_order(self.default_driver_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.delete(get_ride_detail(ride.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_change_rides_status_to_in_process(self):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.get(reverse("taxi:ride-in-process", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @patch("taxi.views.send_message")
    def test_simple_user_cant_change_rides_status_to_finished(
        self, mock_send_message
    ):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.get(reverse("taxi:ride-finished", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        mock_send_message.assert_not_called()


class DriverRideAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.default_driver_user)

    def test_driver_can_list_only_his_orders_or_orders_he_took(self):
        order1 = self.sample_order(self.default_user)
        order2 = self.sample_order(self.default_user)
        order3 = self.sample_order(self.default_driver_user)
        driver_user2 = self.sample_user(
            "another_driver_user@example.com",
            is_driver=True,
        )
        driver2 = self.sample_driver(driver_user2)
        car2 = self.sample_car(driver2)

        ride1 = Ride.objects.create(
            order=order1,
            driver=self.default_driver,
            car=self.default_car,
        )

        ride2 = Ride.objects.create(
            order=order2,
            driver=driver2,
            car=car2,
        )

        ride3 = Ride.objects.create(
            order=order3,
            driver=driver2,
            car=car2,
        )

        serializer1 = RideListSerializer(ride1)
        serializer2 = RideListSerializer(ride2)
        serializer3 = RideListSerializer(ride3)

        res = self.client.get(RIDE_URL)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
        self.assertIn(serializer3.data, res.data)

    def test_driver_cant_delete_rides(self):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.delete(get_ride_detail(ride.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_can_change_ride_status_to_in_process(self):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.get(reverse("taxi:ride-in-process", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch("taxi.views.send_message")
    def test_driver_can_change_ride_status_to_finished(
        self, mock_send_message
    ):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.get(reverse("taxi:ride-finished", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        mock_send_message.assert_called_once()


class AdminRideAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_admin)

    def test_admin_can_list_all_rides(self):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        serializer = RideListSerializer(ride)

        res = self.client.get(RIDE_URL)

        self.assertIn(serializer.data, res.data)

    def test_filter_by_driver(self):
        order1 = self.sample_order(self.default_user)
        order2 = self.sample_order(self.default_user)

        driver_user2 = self.sample_user(
            "another_driver_user@example.com",
            is_driver=True,
        )
        driver2 = self.sample_driver(driver_user2)
        car2 = self.sample_car(driver2)

        ride1 = Ride.objects.create(
            order=order1,
            driver=self.default_driver,
            car=self.default_car,
        )

        ride2 = Ride.objects.create(
            order=order2,
            driver=driver2,
            car=car2,
        )

        serializer1 = RideListSerializer(ride1)
        serializer2 = RideListSerializer(ride2)

        res = self.client.get(RIDE_URL, {"driver": self.default_driver.id})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_by_user(self):
        order1 = self.sample_order(self.default_user)
        user2 = self.sample_user("another_user@example.com")
        order2 = self.sample_order(user2)
        ride1 = Ride.objects.create(
            order=order1,
            driver=self.default_driver,
            car=self.default_car,
        )

        ride2 = Ride.objects.create(
            order=order2,
            driver=self.default_driver,
            car=self.default_car,
        )

        serializer1 = RideListSerializer(ride1)
        serializer2 = RideListSerializer(ride2)

        res = self.client.get(RIDE_URL, {"user": self.default_user.id})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_by_status(self):
        order = self.sample_order(self.default_user)
        order2 = self.sample_order(self.default_user)
        ride1 = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        ride2 = Ride.objects.create(
            order=order2,
            driver=self.default_driver,
            car=self.default_car,
            status="3",
        )

        serializer1 = RideListSerializer(ride1)
        serializer2 = RideListSerializer(ride2)

        res = self.client.get(RIDE_URL, {"status": "3"})

        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer1.data, res.data)

    def test_admin_can_delete_rides(self):
        order = self.sample_order(self.default_user)
        ride = Ride.objects.create(
            order=order,
            driver=self.default_driver,
            car=self.default_car,
        )

        res = self.client.delete(get_ride_detail(ride.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
