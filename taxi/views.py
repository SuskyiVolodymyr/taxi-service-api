from datetime import datetime

from django.db import transaction
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins, status

from payment.services.payment_helper import payment_helper
from taxi.models import City, DriverApplication, Driver, Order, Ride, Car
from taxi.services.filters import (
    CarFilters,
    CityFilters,
    DriverApplicationFilters,
    DriverFilters,
    OrderFilters,
    RideFilters,
)
from taxi.services.permissions import IsAdminOrReadOnly, IsDriverOrAdminUser
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
from taxi.services.telegram_helper import send_message


class CityViewSet(ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = CityFilters


class CarViewSet(ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = [IsDriverOrAdminUser]
    filterset_class = CarFilters

    def get_queryset(self):
        queryset = self.queryset.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(driver__user=self.request.user)
        return queryset


class DriverApplicationViewSet(ModelViewSet):
    queryset = DriverApplication.objects.select_related("user", "city")
    filterset_class = DriverApplicationFilters

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

    def get_permissions(self):
        if self.action in [
            "update",
            "partial_update",
            "destroy",
            "reject",
            "apply",
        ]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(
        detail=True,
        methods=["get"],
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
    queryset = Driver.objects.select_related("user", "city")
    filterset_class = DriverFilters

    def get_serializer_class(self):
        if self.action == "list":
            return DriverListSerializer
        if self.action == "retrieve":
            return DriverDetailSerializer
        return DriverSerializer

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy", "fire"]:
            return [IsAdminUser()]
        return [AllowAny()]

    @action(
        detail=True,
        methods=["get"],
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
    queryset = Order.objects.select_related("user", "city").prefetch_related(
        "payment"
    )
    filterset_class = OrderFilters

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
            if not self.request.user.is_driver:
                queryset = queryset.filter(user=self.request.user)
            else:
                queryset = queryset.filter(
                    Q(payment__status="2")
                    & (Q(user=self.request.user) | Q(is_active=True))
                )
        return queryset

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminUser()]
        if self.action == "take_order":
            return [IsDriverOrAdminUser()]
        return [IsAuthenticated()]

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
    )
    def take_order(self, request, pk: int = None):
        with transaction.atomic():
            order = self.get_object()
            order.is_active = False
            order.save()
            driver = Driver.objects.get(user=self.request.user)
            if Ride.objects.filter(
                driver=driver, status__in=["1", "2"]
            ).exists():
                return Response(
                    "You already have an active ride",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            car_id = request.data.get("car")
            car = Car.objects.get(id=car_id)
            ride = Ride.objects.create(order=order, driver=driver, car=car)
            serializer = RideListSerializer(ride)
            telegram_message = (
                f"Driver {driver.user.full_name} has taken order #{order.id}."
            )
            send_message(telegram_message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class RideViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Ride.objects.all()
    filterset_class = RideFilters

    def get_queryset(self):
        queryset = self.queryset.select_related(
            "order__user",
            "order__city",
            "car",
            "driver__user",
            "order__payment",
            "driver__city",
        )
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

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminUser()]
        if self.action in ["in_process", "finished"]:
            return [IsDriverOrAdminUser()]
        return [IsAuthenticated()]

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
            telegram_message = f"Ride {ride} has been finished."
            send_message(telegram_message)
            return Response(serializer.data, status=status.HTTP_200_OK)
