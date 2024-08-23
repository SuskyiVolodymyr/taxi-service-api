from rest_framework import serializers

from taxi.models import City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name")
