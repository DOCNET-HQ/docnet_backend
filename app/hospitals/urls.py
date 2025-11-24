from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = "hospitals"

router = DefaultRouter()
router.register(r"", views.HospitalStatsViewSet, basename="hospital-stats")


urlpatterns = [
    path("", views.HospitalListView.as_view(), name="hospital-list"),
    path("create/", views.HospitalCreateView.as_view(), name="hospital-create"),
    path("<uuid:id>/", views.HospitalDetailView.as_view(), name="hospital-detail"),
    path(
        "<uuid:id>/update/", views.HospitalUpdateView.as_view(), name="hospital-update"
    ),
    path(
        "<uuid:id>/delete/", views.HospitalDeleteView.as_view(), name="hospital-delete"
    ),
    path(
        "my-profile/", views.MyHospitalProfileView.as_view(), name="my-hospital-profile"
    ),
    path(
        "my-basic-profile/",
        views.MyBasicHospitalProfileView.as_view(),
        name="hospital-basic-info",
    ),
    # Hospital KYC Record CRUD URLs
    path(
        "kyc-records/",
        views.HospitalKYCRecordListView.as_view(),
        name="hospital-kyc-list",
    ),
    path(
        "kyc-records/create/",
        views.HospitalKYCRecordCreateView.as_view(),
        name="hospital-kyc-create",
    ),
    path(
        "kyc-records/<int:id>/",
        views.HospitalKYCRecordDetailView.as_view(),
        name="hospital-kyc-detail",
    ),
    path(
        "kyc-records/<int:id>/update/",
        views.HospitalKYCRecordUpdateView.as_view(),
        name="hospital-kyc-update",
    ),
    path(
        "kyc-records/<int:id>/delete/",
        views.HospitalKYCRecordDeleteView.as_view(),
        name="hospital-kyc-delete",
    ),
    path(
        "<uuid:hospital_id>/kyc-records/",
        views.HospitalKYCRecordsForHospitalView.as_view(),
        name="hospital-kyc-records",
    ),
    # Stats URL
    path("", include(router.urls)),
    path(
        "bulk-update-status/",
        views.bulk_update_hospital_status,
        name="hospital-bulk-update-status",
    ),
]
