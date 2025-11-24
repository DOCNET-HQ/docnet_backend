from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, AppointmentStatsViewSet

app_name = "appointments"

router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")
router.register(
    r"appointment-stats", AppointmentStatsViewSet, basename="appointments-stats"
)

urlpatterns = [
    path("", include(router.urls)),
]
