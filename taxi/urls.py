from django.urls import path
from rest_framework import routers

from taxi.views import (
    CityViewSet,
    DriverApplicationViewSet,
    DriverViewSet,
    OrderViewSet,
)

app_name = "taxi"

router = routers.DefaultRouter()
router.register("cities", CityViewSet)
router.register("driver_applications", DriverApplicationViewSet)
router.register("drivers", DriverViewSet)
router.register("orders", OrderViewSet)

urlpatterns = router.urls
