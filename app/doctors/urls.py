from django.urls import path
from . import views

app_name = "doctors"

urlpatterns = [
    path("", views.DoctorListView.as_view(), name="doctor-list"),
    path("my-doctors/", views.MyDoctorListView.as_view(), name="my-doctor-list"),
    path("create/", views.DoctorCreateView.as_view(), name="doctor-create"),
    path("<uuid:id>/", views.DoctorDetailView.as_view(), name="doctor-detail"),
    path("<uuid:id>/update/", views.DoctorUpdateView.as_view(), name="doctor-update"),
    path("<uuid:id>/delete/", views.DoctorDeleteView.as_view(), name="doctor-delete"),
    path("my-profile/", views.MyDoctorProfileView.as_view(), name="my-doctor-profile"),
    path(
        "my-basic-profile/",
        views.MyBasicDoctorProfileView.as_view(),
        name="doctor-basic-info",
    ),
    # doctor KYC Record CRUD URLs
    path(
        "kyc-records/", views.DoctorKYCRecordListView.as_view(), name="doctor-kyc-list"
    ),
    path(
        "kyc-records/create/",
        views.DoctorKYCRecordCreateView.as_view(),
        name="doctor-kyc-create",
    ),
    path(
        "kyc-records/<int:id>/",
        views.DoctorKYCRecordDetailView.as_view(),
        name="doctor-kyc-detail",
    ),
    path(
        "kyc-records/<int:id>/update/",
        views.DoctorKYCRecordUpdateView.as_view(),
        name="doctor-kyc-update",
    ),
    path(
        "kyc-records/<int:id>/delete/",
        views.DoctorKYCRecordDeleteView.as_view(),
        name="doctor-kyc-delete",
    ),
    path("stats/", views.Doctor_stats, name="doctor-stats"),
]
