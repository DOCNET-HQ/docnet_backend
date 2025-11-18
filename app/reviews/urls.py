from django.urls import path
from . import views

app_name = "reviews"


urlpatterns = [
    path(
        "doctors/<uuid:doctor_id>/has-reviewed/",
        views.HasReviewedDoctorView.as_view(),
        name="has-reviewed-doctor",
    ),
    path(
        "hospitals/<uuid:hospital_id>/has-reviewed/",
        views.HasReviewedHospitalView.as_view(),
        name="has-reviewed-hospital",
    ),
    path(
        "doctors/<uuid:doctor_id>/",
        views.DoctorReviewListCreateView.as_view(),
        name="doctor-reviews-list-create",
    ),
    path(
        "doctor-reviews/<int:pk>/",
        views.DoctorReviewRetrieveUpdateDestroyView.as_view(),
        name="doctor-review-detail",
    ),
    path(
        "hospitals/<uuid:hospital_id>/",
        views.HospitalReviewListCreateView.as_view(),
        name="hospital-reviews-list-create",
    ),
    path(
        "hospital-reviews/<int:pk>/",
        views.HospitalReviewRetrieveUpdateDestroyView.as_view(),
        name="hospital-review-detail",
    ),
]
