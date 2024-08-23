from rest_framework import serializers

from taxi.models import City, DriverApplication, Driver


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
        )
        read_only_fields = ("id", "user")

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
        return driver_application


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ("id", "license_number", "age", "city", "sex", "rate", "user")
