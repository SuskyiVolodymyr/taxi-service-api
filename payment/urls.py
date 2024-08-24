from django.urls import path, include
from rest_framework import routers

from payment.views import (
    PaymentSuccessView,
    PaymentCancelView,
    PaymentViewSet,
)


app_name = "payment"

router = routers.DefaultRouter()
router.register("", PaymentViewSet)

urlpatterns = [
    path(
        "success/<int:pk>/",
        PaymentSuccessView.as_view(),
        name="payment-success",
    ),
    path(
        "cancel/<int:pk>/", PaymentCancelView.as_view(), name="payment-cancel"
    ),
    path("", include(router.urls)),
]
