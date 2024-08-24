from django.db.models import QuerySet
from rest_framework import mixins, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from payment.models import Payment
from payment.serializers import PaymentListSerializer, PaymentSerializer


class PaymentSuccessView(APIView):
    def get(self, request: Request, *args, **kwargs) -> Response:
        order_id = kwargs["pk"]
        payment = Payment.objects.get(order_id=order_id)
        payment.status = "2"
        payment.save()
        return Response(
            {"message": "Payment was successful."}, status=status.HTTP_200_OK
        )


class PaymentCancelView(APIView):
    def get(self, request: Request, *args, **kwargs) -> Response:
        order_id = kwargs["pk"]
        payment = Payment.objects.get(order_id=order_id)
        payment.status = "3"
        payment.save()
        return Response(
            {"message": "Payment was cancelled."}, status=status.HTTP_200_OK
        )


class PaymentViewSet(
    GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):

    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> serializers.SerializerMetaclass:
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.all()
        if not self.request.user.is_staff:
            return queryset.filter(order__user_id=self.request.user.id)
        return queryset
