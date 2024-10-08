from django.db import transaction
from django.db.models import QuerySet
from rest_framework import mixins, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from payment.models import Payment
from payment.serializers import PaymentListSerializer, PaymentSerializer
from payment.services.filters import PaymentFilters
from taxi.services.telegram_helper import send_message


class PaymentSuccessView(APIView):
    """
    Automatically redirects when payment is successful,
    updates payment status and sends a message to the telegram.
    """

    def get(self, request: Request, *args, **kwargs) -> Response:
        with transaction.atomic():
            session_id = request.query_params.get("session_id")
            payment = Payment.objects.get(session_id=session_id)
            payment.status = "2"
            payment.save()
            telegram_message = (
                f"User {payment.order.user.full_name} "
                f"successfully paid for order #{payment.order.id}."
            )
            send_message(telegram_message)
            return Response(
                {"message": "Payment was successful."},
                status=status.HTTP_200_OK,
            )


class PaymentCancelView(APIView):
    """
    Automatically redirects when payment is cancelled,
    updates payment status, removes session url
    and sends a message to the telegram.
    """

    def get(self, request: Request, *args, **kwargs) -> Response:
        with transaction.atomic():
            session_id = request.query_params.get("session_id")

            payment = Payment.objects.get(session_id=session_id)
            payment.status = "3"
            payment.session_url = None
            payment.save()

            order = payment.order
            order.is_active = False
            order.save()

            telegram_message = (
                f"User {payment.order.user.full_name} "
                f"cancelled payment for order #{payment.order.id}."
            )
            send_message(telegram_message)

            return Response(
                {"message": "Payment was cancelled."},
                status=status.HTTP_200_OK,
            )


class PaymentViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):

    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = PaymentFilters

    def get_serializer_class(self) -> serializers.SerializerMetaclass:
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.all()
        if not self.request.user.is_staff:
            return queryset.filter(order__user_id=self.request.user.id)
        return queryset
