from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = "patients"


router = DefaultRouter()
router.register(r"", views.PatientStatsViewSet, basename="patient-stats")


urlpatterns = [
    path("", views.PatientListView.as_view(), name="patient-list"),
    # path(
    #     'create/',
    #     views.PatientCreateView.as_view(),
    #     name='patient-create'
    # ),
    path("<uuid:id>/", views.PatientDetailView.as_view(), name="patient-detail"),
    path("<uuid:id>/update/", views.PatientUpdateView.as_view(), name="patient-update"),
    path("<uuid:id>/delete/", views.PatientDeleteView.as_view(), name="patient-delete"),
    # My Profile URLs
    path(
        "my-profile/", views.MyPatientProfileView.as_view(), name="my-patient-profile"
    ),
    path(
        "my-basic-profile/",
        views.MyBasicPatientProfileView.as_view(),
        name="patient-basic-info",
    ),
    # Patient KYC Record CRUD URLs
    path(
        "kyc-records/",
        views.PatientKYCRecordListView.as_view(),
        name="patient-kyc-list",
    ),
    path(
        "kyc-records/create/",
        views.PatientKYCRecordCreateView.as_view(),
        name="patient-kyc-create",
    ),
    path(
        "kyc-records/<int:id>/",
        views.PatientKYCRecordDetailView.as_view(),
        name="patient-kyc-detail",
    ),
    path(
        "kyc-records/<int:id>/update/",
        views.PatientKYCRecordUpdateView.as_view(),
        name="patient-kyc-update",
    ),
    path(
        "kyc-records/<int:id>/delete/",
        views.PatientKYCRecordDeleteView.as_view(),
        name="patient-kyc-delete",
    ),
    path(
        "<uuid:patient_id>/kyc-records/",
        views.PatientKYCRecordsForPatientView.as_view(),
        name="patient-specific-kyc-records",
    ),
    # Patient Emergency Contact URLs
    path(
        "<uuid:patient_id>/emergency-contacts/",
        views.PatientEmergencyContactListView.as_view(),
        name="patient-emergency-contact-list",
    ),
    path(
        "<uuid:patient_id>/emergency-contacts/create/",
        views.PatientEmergencyContactCreateView.as_view(),
        name="patient-emergency-contact-create",
    ),
    path(
        "<uuid:patient_id>/emergency-contacts/<int:id>/",
        views.PatientEmergencyContactDetailView.as_view(),
        name="patient-emergency-contact-detail",
    ),
    # Stats URL
    path("", include(router.urls)),
]
