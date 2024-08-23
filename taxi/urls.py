from rest_framework import routers

from taxi.views import CityViewSet

app_name = "taxi"

router = routers.DefaultRouter()
router.register("cities", CityViewSet)

urlpatterns = router.urls
