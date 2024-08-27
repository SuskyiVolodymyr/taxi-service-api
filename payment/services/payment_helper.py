import stripe
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from payment.models import Payment
from payment.serializers import PaymentSerializer
from taxi.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

PRICE_PER_METER = 1


def payment_helper(order: Order) -> Response:
    money_to_pay = order.distance * PRICE_PER_METER
    with transaction.atomic():
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": order},
                            "unit_amount": money_to_pay,
                        },
                        "quantity": 1,
                    },
                ],
                mode="payment",
                success_url=settings.SITE_DOMAIN
                + "api/v1/payment/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.SITE_DOMAIN
                + "api/v1/payment/cancel?session_id={CHECKOUT_SESSION_ID}",
            )

            payment = Payment.objects.create(
                status="1",
                order=order,
                session_url=checkout_session.url,
                session_id=checkout_session.id,
                money_to_pay=round(money_to_pay / 100, 2),
            )

            serializer = PaymentSerializer(payment)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
