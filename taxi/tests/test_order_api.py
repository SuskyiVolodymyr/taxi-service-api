from unittest.mock import patch

from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from payment.models import Payment
from taxi.models import Order, City, Driver, Car, Ride
from taxi.serializers import OrderListSerializer
from taxi.tests.base import TestBase

ORDER_URL = reverse("taxi:order-list")


def get_order_detail(order_id) -> str:
    return reverse("taxi:order-detail", args=[order_id])


class UnauthorizedOrderAPITest(TestBase):
    def test_unauthorized_user_cant_list_orders(self):
        res = self.client.get(ORDER_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_create_orders(self):
        payload = {
            "city": "test city",
            "street_from": "test street_from",
            "street_to": "test street_to",
            "distance": 51,
        }
        res = self.client.post(ORDER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_delete_orders(self):
        order = self.sample_order(self.default_user)

        res = self.client.delete(get_order_detail(order.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SimpleUserOrderAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_user)

    def test_simple_user_can_list_only_his_orders(self):
        another_user = self.sample_user("test2@test.com")
        order1 = self.sample_order(self.default_user)
        order2 = self.sample_order(another_user)
        serializer1 = OrderListSerializer(order1)
        serializer2 = OrderListSerializer(order2)
        res = self.client.get(ORDER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    @patch("taxi.serializers.send_message")
    @patch("taxi.views.payment_helper")
    def test_simple_user_can_create_orders(
        self, mock_payment_helper, mock_send_message
    ):
        mock_payment_helper.return_value = Response(
            status=status.HTTP_201_CREATED
        )
        payload = {
            "city": self.default_city.id,
            "street_from": "test street_from",
            "street_to": "test street_to",
            "distance": 51,
        }
        self.client.post(ORDER_URL, payload)

        mock_payment_helper.assert_called_once()
        mock_send_message.assert_called_once()
        self.assertTrue(Order.objects.exists())

    @patch("taxi.serializers.send_message")
    @patch("taxi.views.payment_helper")
    def test_distance_validation_for_orders(
        self, mock_payment_helper, mock_send_message
    ):
        mock_payment_helper.return_value = Response(
            status=status.HTTP_201_CREATED
        )
        payload = {
            "city": self.default_city.id,
            "street_from": "test street_from",
            "street_to": "test street_to",
            "distance": 49,
        }
        res = self.client.post(ORDER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        mock_payment_helper.assert_not_called()
        mock_send_message.assert_not_called()

    def test_simple_user_can_have_only_one_active_order(self):
        self.sample_order(self.default_user)
        payload = {
            "city": self.default_city.id,
            "street_from": "test street_from",
            "street_to": "test street_to",
            "distance": 51,
        }

        res = self.client.post(ORDER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_simple_user_cant_delete_orders(self):
        order = self.sample_order(self.default_user)

        res = self.client.delete(get_order_detail(order.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class DriverOrderAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_driver_user)

    @patch("taxi.views.send_message")
    def test_driver_can_take_order(self, mock_send_message):
        order = self.sample_order(self.default_user)
        Payment.objects.create(
            status="2",
            order=order,
            session_id="123",
            money_to_pay=50,
        )

        res = self.client.post(
            reverse("taxi:order-take-order", args=[order.id]),
            {"car": self.default_car.id},
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        order.refresh_from_db()
        self.assertFalse(order.is_active)
        self.assertTrue(Ride.objects.exists())
        mock_send_message.assert_called_once()

    def test_driver_cant_take_order_if_has_active_ride(self):
        order1 = self.sample_order(self.default_user)
        Ride.objects.create(
            order=order1,
            driver=self.default_driver,
            car=self.default_car,
        )
        order2 = self.sample_order(self.default_user)
        Payment.objects.create(
            status="2",
            order=order2,
            session_id="123",
            money_to_pay=50,
        )

        res = self.client.post(
            reverse("taxi:order-take-order", args=[order2.id]),
            {"car": self.default_car.id},
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_cant_delete_orders(self):
        order = self.sample_order(self.default_user)

        res = self.client.delete(get_order_detail(order.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminOrderAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_admin)

    def test_admin_can_list_all_orders(self):
        order = self.sample_order(self.default_user)

        res = self.client.get(ORDER_URL)

        serializer = OrderListSerializer(order)

        self.assertIn(serializer.data, res.data)

    def test_filter_by_payment_status(self):
        order1 = self.sample_order(self.default_user)
        Payment.objects.create(
            status="2",
            order=order1,
            session_id="123",
            money_to_pay=50,
        )
        order2 = self.sample_order(self.default_user)
        Payment.objects.create(
            status="1",
            order=order2,
            session_id="123",
            money_to_pay=50,
        )

        serializer1 = OrderListSerializer(order1)
        serializer2 = OrderListSerializer(order2)

        res = self.client.get(ORDER_URL, {"payment_status": "2"})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_by_user(self):
        order1 = self.sample_order(self.default_user)
        order2 = self.sample_order(self.default_driver_user)

        serializer1 = OrderListSerializer(order1)
        serializer2 = OrderListSerializer(order2)

        res = self.client.get(ORDER_URL, {"user": self.default_driver_user.id})

        self.assertNotIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)

    def test_filter_by_is_active(self):
        order1 = self.sample_order(self.default_user)
        order2 = self.sample_order(self.default_user)
        order2.is_active = False
        order2.save()

        serializer1 = OrderListSerializer(order1)
        serializer2 = OrderListSerializer(order2)

        res = self.client.get(ORDER_URL, {"is_active": "true"})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_update_orders_method_not_allowed(self):
        order = self.sample_order(self.default_user)

        payload = {
            "city": self.default_city.id,
            "street_from": "test street_from updated",
            "street_to": "test street_to",
            "distance": 51,
        }

        res = self.client.patch(get_order_detail(order.id), payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_admin_can_delete_orders(self):
        order = self.sample_order(self.default_user)

        res = self.client.delete(get_order_detail(order.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
