from rest_framework.viewsets import ModelViewSet

from taxi.models import City
from taxi.permissions import IsAdminOrReadOnly
from taxi.serializers import CitySerializer


class CityViewSet(ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAdminOrReadOnly]
