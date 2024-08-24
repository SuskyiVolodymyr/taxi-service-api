from rest_framework import serializers

from payment.models import Payment
from taxi.serializers import OrderSerializer


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    status = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "order",
            "session_url",
            "session_id",
            "money_to_pay",
        )


class PaymentListSerializer(PaymentSerializer):

    class Meta:
        model = Payment
        fields = ("id", "status", "order", "money_to_pay")
