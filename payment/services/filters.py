import django_filters

from payment.models import Payment


class PaymentFilters(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=[("1", "Pending"), ("2", "Paid"), ("3", "Canceled")],
        label="Status",
    )
    user = django_filters.NumberFilter(field_name="order__user__id")

    class Meta:
        model = Payment
        fields = ["status", "user"]
