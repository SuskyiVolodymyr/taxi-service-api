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
        self.client.force_authenticate(self.admin)
        self.city = City.objects.create(name="test city")

    def sample_order(self):
        return Order.objects.create(
            user=self.user,
            city=City.objects.create(name="test city"),
            street_from="test street_from",
            street_to="test street_to",
            distance=51,
        )

    def sample_driver(self):
        return Driver.objects.create(
            user=self.user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def sample_car(self, driver):
        return Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

    def test_create_method_not_allowed(self):
        order = self.sample_order()
        driver = self.sample_driver()
        car = self.sample_car(driver)

        payload = {"order": order.id, "driver": driver.id, "car": car.id}

        res = self.client.post(RIDE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_method_not_allowed(self):
        order = self.sample_order()
        driver = self.sample_driver()
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        payload = {"order": order.id, "driver": driver.id, "car": car.id}

        res = self.client.patch(get_ride_detail(ride.id), payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UnauthorizedRideAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.city = City.objects.create(name="test city")

    def sample_order(self):
        return Order.objects.create(
            user=self.user,
            city=City.objects.create(name="test city"),
            street_from="test street_from",
            street_to="test street_to",
            distance=51,
        )

    def sample_driver(self):
        return Driver.objects.create(
            user=self.user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def sample_car(self, driver):
        return Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

    def test_unauthorized_cant_list_rides(self):
        res = self.client.get(RIDE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_cant_delete_rides(self):
        order = self.sample_order()
        driver = self.sample_driver()
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.delete(get_ride_detail(ride.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_cant_change_rides_status_to_in_process(self):
        order = self.sample_order()
        driver = self.sample_driver()
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.get(reverse("taxi:ride-in-process", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("taxi.views.send_message")
    def test_unauthorized_cant_change_rides_status_to_finished(
        self, mock_send_message
    ):
        order = self.sample_order()
        driver = self.sample_driver()
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.get(reverse("taxi:ride-finished", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_send_message.assert_not_called()


class SimpleUserRideAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)
        self.city = City.objects.create(name="test city")
        self.driver_user = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )
        self.driver_user.is_driver = True
        self.driver_user.save()
        self.user2 = get_user_model().objects.create_user(
            email="test3@test.com",
            first_name="test3",
            last_name="test3",
            password="test1234",
        )

    def sample_order(self, user: AUTH_USER_MODEL):
        return Order.objects.create(
            user=user,
            city=City.objects.create(name="test city"),
            street_from="test street_from",
            street_to="test street_to",
            distance=51,
        )

    def sample_driver(self):
        return Driver.objects.create(
            user=self.driver_user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def sample_car(self, driver):
        return Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

    def test_simple_user_can_list_rides(self):
        res = self.client.get(RIDE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_simple_user_can_list_only_his_rides(self):
        order1 = self.sample_order(self.user)
        order2 = self.sample_order(self.user2)
        driver = self.sample_driver()
        car = self.sample_car(driver)

        ride1 = Ride.objects.create(
            order=order1,
            driver=driver,
            car=car,
        )

        ride2 = Ride.objects.create(
            order=order2,
            driver=driver,
            car=car,
        )

        serializer1 = RideListSerializer(ride1)
        serializer2 = RideListSerializer(ride2)

        res = self.client.get(RIDE_URL)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_simple_user_cant_delete_rides(self):
        order = self.sample_order(self.user)
        driver = self.sample_driver()
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.delete(get_ride_detail(ride.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_change_rides_status_to_in_process(self):
        order = self.sample_order(self.user)
        driver = self.sample_driver()
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.get(reverse("taxi:ride-in-process", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @patch("taxi.views.send_message")
    def test_simple_user_cant_change_rides_status_to_in_process(
        self, mock_send_message
    ):
        order = self.sample_order(self.user)
        driver = self.sample_driver()
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.get(reverse("taxi:ride-finished", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        mock_send_message.assert_not_called()


class DriverRideAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)
        self.user.is_driver = True
        self.user.save()
        self.user2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test",
            last_name="test",
            password="test1234",
        )
        self.driver2 = get_user_model().objects.create_user(
            email="test3@test.com",
            first_name="test3",
            last_name="test3",
            password="test1234",
            is_driver=True,
        )
        self.city = City.objects.create(name="test city")

    def sample_order(self, user: AUTH_USER_MODEL):
        return Order.objects.create(
            user=user,
            city=self.city,
            street_from="test street_from",
            street_to="test street_to",
            distance=51,
        )

    def sample_driver(self, user: AUTH_USER_MODEL):
        return Driver.objects.create(
            user=user,
            license_number="123456",
            age=18,
            city=self.city,
            sex="M",
        )

    def sample_car(self, driver):
        return Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

    def test_driver_can_list_only_his_orders_or_orders_he_took(self):
        order1 = self.sample_order(self.user2)
        order2 = self.sample_order(self.user2)
        order3 = self.sample_order(self.user)
        driver1 = self.sample_driver(self.user)
        driver2 = self.sample_driver(self.driver2)

        car1 = self.sample_car(driver1)
        car2 = self.sample_car(driver2)

        ride1 = Ride.objects.create(
            order=order1,
            driver=driver1,
            car=car1,
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
        order = self.sample_order(self.user2)
        driver = self.sample_driver(self.user)
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.delete(get_ride_detail(ride.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_can_change_ride_status_to_in_process(self):
        order = self.sample_order(self.user2)
        driver = self.sample_driver(self.user)
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.get(reverse("taxi:ride-in-process", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch("taxi.views.send_message")
    def test_driver_can_change_ride_status_to_finished(
        self, mock_send_message
    ):
        order = self.sample_order(self.user2)
        driver = self.sample_driver(self.user)
        car = self.sample_car(driver)

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.get(reverse("taxi:ride-finished", args=[ride.id]))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        mock_send_message.assert_called_once()


class AdminRideAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin)

    def test_admin_can_delete_rides(self):
        order = Order.objects.create(
            user=self.user,
            city=City.objects.create(name="test city"),
            street_from="test street_from",
            street_to="test street_to",
            distance=51,
        )

        driver = Driver.objects.create(
            user=get_user_model().objects.create_user(
                email="test2@test.com",
                first_name="test",
                last_name="test",
                password="test1234",
                is_driver=True,
            ),
            license_number="123456",
            age=18,
            city=City.objects.create(name="test city"),
            sex="M",
        )
        car = Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

        ride = Ride.objects.create(
            order=order,
            driver=driver,
            car=car,
        )

        res = self.client.delete(get_ride_detail(ride.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
