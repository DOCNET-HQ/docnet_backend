from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import AdminProfile
from .serializers import (
    AdminSerializer,
    BasicAdminSerializer,
    AdminUpdateSerializer,
    AdminListSerializer,
)
from utils.pagination import StandardResultsSetPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


# Admin Views
class AdminListView(generics.ListAPIView):
    """
    List all admins with filtering and search capabilities
    """

    queryset = AdminProfile.objects.all()
    serializer_class = AdminListSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["user__email", "country", "state", "city"]
    search_fields = [
        "name",
        "user__email",
        "phone_number",
        "country",
        "state",
        "city",
    ]
    ordering_fields = [
        "name",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Additional custom filtering can be added here
        return queryset.select_related("user")


class AdminDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single admin by ID
    """

    queryset = AdminProfile.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().select_related("user")


class AdminUpdateView(generics.UpdateAPIView):
    """
    Update admin information (PUT and PATCH)
    """

    queryset = AdminProfile.objects.all()
    serializer_class = AdminUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = "id"

    def get_object(self):
        # Users can only update their own admin profile
        obj = get_object_or_404(AdminProfile, id=self.kwargs["id"])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class AdminDeleteView(generics.DestroyAPIView):
    """
    Delete a admin profile
    """

    queryset = AdminProfile.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = "id"

    def get_object(self):
        # Users can only delete their own admin profile
        # Admin can delete any
        obj = get_object_or_404(AdminProfile, id=self.kwargs["id"])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class MyAdminProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current Admin's profile
    """

    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        try:
            return AdminProfile.objects.get(user=self.request.user)
        except AdminProfile.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Admin's profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return AdminUpdateSerializer
        return AdminSerializer


class MyBasicAdminProfileView(generics.RetrieveAPIView):
    """
    Get the current user's basic admin profile info
    """

    serializer_class = BasicAdminSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self):
        try:
            return AdminProfile.objects.get(user=self.request.user)
        except AdminProfile.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Admin profile not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
