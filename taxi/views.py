from datetime import datetime

from django.db import transaction
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins, status

from payment.payment_helper import payment_helper
from taxi.models import City, DriverApplication, Driver, Order, Ride, Car
from taxi.permissions import IsAdminOrReadOnly, IsDriverOrAdminUser
from taxi.serializers import (
    CitySerializer,
    DriverApplicationSerializer,
    DriverSerializer,
    DriverApplicationListSerializer,
    DriverApplicationDetailSerializer,
    OrderSerializer,
    TakeOrderSerializer,
    RideListSerializer,
    CarSerializer,
    DriverListSerializer,
    DriverDetailSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    RideDetailSerializer,
)


class CityViewSet(ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAdminOrReadOnly]


class CarViewSet(ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = [IsDriverOrAdminUser]

    def get_queryset(self):
        queryset = self.queryset.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(driver__user=self.request.user)
        return queryset


class DriverApplicationViewSet(ModelViewSet):
    queryset = DriverApplication.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return DriverApplicationListSerializer
        if self.action == "retrieve":
            return DriverApplicationDetailSerializer
        return DriverApplicationSerializer

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
            user.save()
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
            serializer = self.get_serializer_class()(application)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class DriverViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Driver.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return DriverListSerializer
        if self.action == "retrieve":
            return DriverDetailSerializer
        return DriverSerializer

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
            user.save()
            driver.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "take_order":
            return TakeOrderSerializer
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(user=self.request.user) | Q(is_active=True)
            )
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return payment_helper(order=serializer.instance)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsDriverOrAdminUser],
    )
    def take_order(self, request, pk: int = None):
        with transaction.atomic():
            order = self.get_object()
            order.is_active = False
            order.save()
            driver = Driver.objects.get(user=self.request.user)
            car_id = request.data.get("car")
            car = Car.objects.get(id=car_id)
            ride = Ride.objects.create(order=order, driver=driver, car=car)
            serializer = RideListSerializer(ride)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class RideViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Ride.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.all()
        if not self.request.user.is_staff and not self.request.user.is_driver:
            queryset = queryset.filter(order__user=self.request.user)
        elif self.request.user.is_driver:
            queryset = queryset.filter(
                Q(driver__user=self.request.user)
                | Q(order__user=self.request.user)
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RideDetailSerializer
        return RideListSerializer

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsDriverOrAdminUser],
    )
    def in_process(self, request, pk: int = None):
        with transaction.atomic():
            ride = self.get_object()
            ride.status = "2"
            ride.save()
            serializer = self.get_serializer_class()(ride)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsDriverOrAdminUser],
    )
    def finished(self, request, pk: int = None):
        with transaction.atomic():
            ride = self.get_object()
            ride.status = "3"
            ride.save()
            serializer = self.get_serializer_class()(ride)
            return Response(serializer.data, status=status.HTTP_200_OK)
