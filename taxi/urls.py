from django.urls import path
from rest_framework import routers

from taxi.views import CityViewSet, DriverApplicationViewSet, DriverViewSet

app_name = "taxi"

router = routers.DefaultRouter()
router.register("cities", CityViewSet)
router.register("driver_applications", DriverApplicationViewSet)
router.register("drivers", DriverViewSet)

# urlpatterns = [
#     path("driver_applications/", DriverApplicationViewSet.as_view(), name="driver_applications"),
# ]

urlpatterns = router.urls
