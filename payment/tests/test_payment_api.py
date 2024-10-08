from unittest.mock import patch

from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from payment.models import Payment
from payment.serializers import PaymentListSerializer
from taxi.models import Order, City

PAYMENT_URL = reverse("payment:payment-list")


def get_payment_detail(payment_id) -> str:
    return reverse("payment:payment-detail", args=[payment_id])


class BaseTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@admin.com",
            first_name="admin",
            last_name="admin",
            password="admin1234",
        )
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            first_name="test",
            last_name="test",
            password="test1234",
        )

    @staticmethod
    def sample_order(user: AUTH_USER_MODEL) -> Order:
        return Order.objects.create(
            user=user,
            city=City.objects.create(name="test city"),
            street_from="test street_from",
            street_to="test street_to",
            distance=51,
        )

    @staticmethod
    def sample_payment(order: Order) -> Payment:
        return Payment.objects.create(
            status="1",
            session_url="https://google.com",
            session_id="test",
            money_to_pay=10.00,
            order=order,
        )


class TestAllowedMethods(BaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.admin)

    def test_list_method_allowed(self):
        res = self.client.get(PAYMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_method_allowed(self):
        order = self.sample_order(self.user)
        payment = self.sample_payment(order)

        res = self.client.get(get_payment_detail(payment.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_method_not_allowed(self):
        res = self.client.post(PAYMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_method_not_allowed(self):
        order = self.sample_order(self.user)
        payment = self.sample_payment(order)

        res = self.client.put(get_payment_detail(payment.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_method_not_allowed(self):
        order = self.sample_order(self.user)
        payment = self.sample_payment(order)

        res = self.client.delete(get_payment_detail(payment.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UnauthorizedUserPaymentAPITest(BaseTest):

    def test_unauthorized_user_list_method_not_allowed(self):
        res = self.client.get(PAYMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_retrieve_method_not_allowed(self):
        order = self.sample_order(self.user)
        payment = self.sample_payment(order)

        res = self.client.get(get_payment_detail(payment.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SimpleUserPaymentAPITest(BaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)

    def test_simple_user_list_method_allowed(self):
        res = self.client.get(PAYMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_simple_user_can_list_only_his_payments(self):
        order1 = self.sample_order(self.user)
        another_user = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )
        order2 = self.sample_order(another_user)
        payment1 = self.sample_payment(order1)
        payment2 = self.sample_payment(order2)

        serializer1 = PaymentListSerializer(payment1)
        serializer2 = PaymentListSerializer(payment2)

        res = self.client.get(PAYMENT_URL)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    @patch("payment.views.send_message")
    def test_success_payment(self, mock_send_message):
        order = self.sample_order(self.user)
        payment = self.sample_payment(order)

        res = self.client.get(
            reverse("payment:payment-success")
            + f"?session_id={payment.session_id}"
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        payment.refresh_from_db()

        self.assertEqual(payment.status, "2")

        mock_send_message.assert_called_once()

    @patch("payment.views.send_message")
    def test_canceled_payment(self, mock_send_message):
        order = self.sample_order(self.user)
        payment = self.sample_payment(order)

        res = self.client.get(
            reverse("payment:payment-cancel")
            + f"?session_id={payment.session_id}"
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        payment.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(payment.status, "3")
        self.assertIsNone(payment.session_url)
        self.assertFalse(order.is_active)

        mock_send_message.assert_called_once()


class AdminPaymentAPITest(BaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.admin)

    def test_admin_can_list_all_payments(self):
        order = self.sample_order(self.user)
        payment = self.sample_payment(order)

        serializer = PaymentListSerializer(payment)

        res = self.client.get(PAYMENT_URL)

        self.assertIn(serializer.data, res.data)

    def test_filter_by_status(self):
        order1 = self.sample_order(self.user)
        user2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )
        order2 = self.sample_order(user2)

        payment1 = self.sample_payment(order1)
        payment2 = self.sample_payment(order2)

        payment2.status = "3"
        payment2.save()

        serializer1 = PaymentListSerializer(payment1)
        serializer2 = PaymentListSerializer(payment2)

        res = self.client.get(PAYMENT_URL, {"status": "3"})

        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer1.data, res.data)

    def test_filter_by_user(self):
        order1 = self.sample_order(self.user)
        user2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )
        order2 = self.sample_order(user2)

        payment1 = self.sample_payment(order1)
        payment2 = self.sample_payment(order2)

        serializer1 = PaymentListSerializer(payment1)
        serializer2 = PaymentListSerializer(payment2)

        res = self.client.get(PAYMENT_URL, {"user": user2.id})

        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer1.data, res.data)
