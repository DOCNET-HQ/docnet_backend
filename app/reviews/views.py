from reviews.serializers import (
    DoctorReviewSerializer,
    HospitalReviewSerializer,
    DoctorReviewCreateSerializer,
    HospitalReviewCreateSerializer,
)
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from reviews.pagination import ReviewsPagination
from .models import DoctorReview, HospitalReview
from django.db.models import Case, When, BooleanField
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


class HasReviewedDoctorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id):
        has_reviewed = DoctorReview.objects.filter(
            user=request.user, doctor_id=doctor_id
        ).exists()
        return Response({"has_reviewed": has_reviewed})


class HasReviewedHospitalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, hospital_id):
        has_reviewed = HospitalReview.objects.filter(
            user=request.user, hospital_id=hospital_id
        ).exists()
        return Response({"has_reviewed": has_reviewed})


class DoctorReviewListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ReviewsPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DoctorReviewCreateSerializer
        return DoctorReviewSerializer

    def get_queryset(self):
        doctor_id = self.kwargs.get("doctor_id")
        queryset = DoctorReview.objects.filter(doctor_id=doctor_id)

        # Annotate if review belongs to authenticated user
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_auth_user_review=Case(
                    When(user=self.request.user, then=True),
                    default=False,
                    output_field=BooleanField(),
                )
            ).order_by("-is_auth_user_review", "-created_at")

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HospitalReviewListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ReviewsPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return HospitalReviewCreateSerializer
        return HospitalReviewSerializer

    def get_queryset(self):
        hospital_id = self.kwargs.get("hospital_id")
        queryset = HospitalReview.objects.filter(hospital_id=hospital_id)

        # Annotate if review belongs to authenticated user
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_auth_user_review=Case(
                    When(user=self.request.user, then=True),
                    default=False,
                    output_field=BooleanField(),
                )
            ).order_by("-is_auth_user_review", "-created_at")

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DoctorReviewRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorReviewSerializer
    queryset = DoctorReview.objects.all()

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied("You can only update your own reviews.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied("You can only delete your own reviews.")
        return super().destroy(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class HospitalReviewRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HospitalReviewSerializer
    queryset = HospitalReview.objects.all()

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied("You can only update your own reviews.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied("You can only delete your own reviews.")
        return super().destroy(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
