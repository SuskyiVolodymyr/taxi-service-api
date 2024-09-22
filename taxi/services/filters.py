import django_filters

from taxi.models import Car, City, DriverApplication, Driver, Order, Ride


class CarFilters(django_filters.FilterSet):
    driver = django_filters.NumberFilter(field_name="driver__id")

    class Meta:
        model = Car
        fields = ["driver"]


class CityFilters(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = City
        fields = ["name"]


class DriverApplicationFilters(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=[("P", "Pending"), ("A", "Approved"), ("R", "Rejected")],
        label="Status",
    )

    class Meta:
        model = DriverApplication
        fields = ["status"]


class DriverFilters(django_filters.FilterSet):
    city = django_filters.NumberFilter(field_name="city__id")
    first_name = django_filters.CharFilter(
        field_name="user__first_name", lookup_expr="icontains"
    )
    last_name = django_filters.CharFilter(
        field_name="user__last_name", lookup_expr="icontains"
    )

    class Meta:
        model = Driver
        fields = ["city", "first_name", "last_name"]


class OrderFilters(django_filters.FilterSet):
    payment_status = django_filters.ChoiceFilter(
        field_name="payment__status",
        choices=[("1", "Pending"), ("2", "Paid"), ("3", "Canceled")],
        label="Payment Status",
    )
    user = django_filters.NumberFilter(field_name="user__id")

    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Order
        fields = ["payment_status", "user", "is_active"]


class RideFilters(django_filters.FilterSet):
    driver = django_filters.NumberFilter(field_name="driver__id")
    user = django_filters.NumberFilter(field_name="order__user__id")
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=[
            ("1", "Waiting for client"),
            ("2", "In process"),
            ("3", "Finished"),
        ],
        label="Status",
    )

    class Meta:
        model = Ride
        fields = ["driver", "user", "status"]
