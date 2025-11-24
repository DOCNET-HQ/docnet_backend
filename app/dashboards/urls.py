from django.urls import path
from dashboards.views import (
    AdminDashboardView,
    HospitalDashboardView,
    DoctorDashboardView,
)

urlpatterns = [
    path("admin-stats/", AdminDashboardView.as_view(), name="admin-dashboard-stats"),
    path("hospital-stats/", HospitalDashboardView.as_view(), name="hospital-dashboard"),
    path("doctor-stats/", DoctorDashboardView.as_view(), name="doctor-dashboard"),
]
