from datetime import datetime

from django.db import transaction
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins, status

from taxi.models import City, DriverApplication, Driver
from taxi.permissions import IsAdminOrReadOnly
from taxi.serializers import (
    CitySerializer,
    DriverApplicationSerializer,
    DriverSerializer,
)


class CityViewSet(ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAdminOrReadOnly]


class DriverApplicationViewSet(ModelViewSet):
    queryset = DriverApplication.objects.all()
    serializer_class = DriverApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAdminUser],
    )
    def apply(self, request, pk: int = None):
        with transaction.atomic():
            application = self.get_object()
            if application.status != "P":
                return Response(
                    "Application already processed",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = application.user
            driver = Driver.objects.create(
                user=user,
                license_number=application.license_number,
                age=application.age,
                city=application.city,
                sex=application.sex,
            )
            user.is_driver = True
            application.status = "A"
            application.reviewed_at = datetime.now()
            application.save()
            driver_serializer = DriverSerializer(driver)
            return Response(
                driver_serializer.data, status=status.HTTP_201_CREATED
            )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAdminUser],
    )
    def reject(self, request, pk: int = None):
        with transaction.atomic():
            application = self.get_object()
            if application.status != "P":
                return Response(
                    "Application already processed",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            application.status = "R"
            application.reviewed_at = datetime.now()
            application.save()
            serializer = DriverApplicationSerializer(application)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class DriverViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAdminUser],
    )
    def fire(self, request, pk: int = None):
        with transaction.atomic():
            driver = self.get_object()
            user = driver.user
            user.is_driver = False
            driver.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
