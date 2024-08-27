from rest_framework import serializers

from payment.models import Payment
from taxi.models import City, DriverApplication, Driver, Order, Ride, Car
from taxi.services.telegram_helper import send_message
from user.serializers import UserSerializer


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name")


class DriverApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverApplication
        fields = (
            "id",
            "license_number",
            "age",
            "city",
            "sex",
            "user",
            "status",
            "created_at",
            "reviewed_at",
        )
        read_only_fields = (
            "id",
            "user",
            "status",
            "created_at",
            "reviewed_at",
        )

    def validate(self, attrs):
        if attrs["age"] < 18:
            raise serializers.ValidationError(
                "Driver must be at least 18 years old"
            )
        if self.context["request"].user.is_driver:
            raise serializers.ValidationError("User is already a driver")
        existing_application = DriverApplication.objects.filter(
            user=self.context["request"].user, status="P"
        )
        if existing_application:
            raise serializers.ValidationError(
                "User already applied for a driver"
            )
        return attrs

    def create(self, validated_data):
        driver_application = DriverApplication.objects.create(
            user=self.context["request"].user, **validated_data
        )
        telegram_message = f"User {self.context['request'].user.full_name} applied for a driver"
        send_message(telegram_message)
        return driver_application


class DriverApplicationListSerializer(DriverApplicationSerializer):
    user = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="full_name",
    )
    city = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = DriverApplication
        fields = (
            "id",
            "user",
            "city",
            "status",
            "created_at",
            "reviewed_at",
        )


class DriverApplicationDetailSerializer(DriverApplicationSerializer):
    user = UserSerializer(many=False)
    city = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )
    status = serializers.CharField(source="get_status_display")
    sex = serializers.CharField(source="get_sex_display")


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ("id", "license_number", "age", "city", "sex", "rate", "user")


class DriverListSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="full_name",
    )

    class Meta:
        model = Driver
        fields = ("id", "user", "rate")


class DriverDetailSerializer(DriverSerializer):
    user = UserSerializer(many=False, read_only=True)
    city = CitySerializer(many=False, read_only=True)
    sex = serializers.CharField(source="get_sex_display")


class CarSerializer(serializers.ModelSerializer):
    driver = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="user.full_name",
    )

    class Meta:
        model = Car
        fields = ("id", "model", "number", "driver")
        read_only_fields = ("id", "driver")

    def create(self, validated_data):
        driver = Driver.objects.get(user=self.context["request"].user)
        car = Car.objects.create(driver=driver, **validated_data)
        return car


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "id",
            "city",
            "user",
            "street_from",
            "street_to",
            "distance",
            "date_created",
            "is_active",
        )
        read_only_fields = ("id", "user", "date_created", "is_active")

    def validate(self, attrs):
        if Order.objects.filter(
            user=self.context["request"].user, is_active=True
        ):
            raise serializers.ValidationError(
                "User already has an active order"
            )
        if Payment.objects.filter(
            order__user=self.context["request"].user, status="1"
        ):
            raise serializers.ValidationError(
                "You can`t create an order with pending payment"
            )
        if attrs["distance"] < 50:
            raise serializers.ValidationError(
                "Distance must be at least 50 meters"
            )
        return attrs

    def create(self, validated_data):
        order = Order.objects.create(
            user=self.context["request"].user, **validated_data
        )
        telegram_message = (
            f"User {self.context['request'].user.full_name} created an order\n"
            f"City: {order.city.name}\n"
            f"From: {order.street_from}\nTo: {order.street_to}\n"
            f"Distance: {order.distance} meters"
            f"Order_id {order.id}"
        )
        send_message(telegram_message)
        return order


class OrderListSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="full_name",
    )
    payment_status = serializers.CharField(source="payment.get_status_display")

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "distance",
            "date_created",
            "is_active",
            "payment_status",
        )


class OrderDetailSerializer(serializers.ModelSerializer):
    city = CitySerializer(many=False, read_only=True)
    user = UserSerializer(many=False, read_only=True)
    payment_status = serializers.CharField(source="payment.get_status_display")

    class Meta:
        model = Order
        fields = (
            "id",
            "city",
            "user",
            "street_from",
            "street_to",
            "distance",
            "date_created",
            "is_active",
            "payment_status",
        )


class TakeOrderSerializer(serializers.ModelSerializer):
    car = serializers.PrimaryKeyRelatedField(queryset=Car.objects.none())

    class Meta:
        model = Ride
        fields = ("car",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context["request"].user
        self.fields["car"].queryset = Car.objects.filter(driver__user=user)


class RideListSerializer(serializers.ModelSerializer):
    driver = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="user__full_name",
    )
    car = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="number",
    )
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = Ride
        fields = ("id", "order", "driver", "car", "status")


class RideDetailSerializer(RideListSerializer):
    order = OrderDetailSerializer(many=False, read_only=True)
    driver = DriverDetailSerializer(many=False, read_only=True)
    car = CarSerializer(many=False, read_only=True)
