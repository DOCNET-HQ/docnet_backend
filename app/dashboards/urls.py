from django.urls import path
from dashboards.views import AdminDashboardView, HospitalDashboardView

urlpatterns = [
    path("admin-stats/", AdminDashboardView.as_view(), name="admin-dashboard-stats"),
    path("hospital-stats/", HospitalDashboardView.as_view(), name="hospital-dashboard"),
]
