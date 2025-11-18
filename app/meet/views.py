from meet.models import Meet
from meet.serializers import (
    MeetSerializer,
    MeetCalendarSerializer,
    MeetTokenCreateSerializer,
    MeetTokenResponseSerializer,
)
from django.conf import settings
from meet.filters import MeetFilter
from rest_framework import generics
from meet.utils import generate_meet_token
from rest_framework.response import Response
from rest_framework.views import APIView, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


class MeetDetailView(APIView):
    """API view to retrieve Meet details."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MeetSerializer})
    def get(self, request, meet_id):
        try:
            meet = Meet.objects.get(id=meet_id)
        except Meet.DoesNotExist:
            return Response(
                {"detail": "Meet not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is in members list
        if request.user not in meet.members.all():
            return Response(
                {"detail": "You are not a member of this meeting."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = MeetSerializer(meet)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MeetTokenCreateView(APIView):
    """API view to create a Meet token."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=MeetTokenCreateSerializer,
        responses={201: MeetTokenResponseSerializer},
    )
    def post(self, request):
        serializer = MeetTokenCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        channel_name = serializer.validated_data["channel_name"]

        try:
            meet = Meet.objects.get(channel_name=channel_name)
        except Meet.DoesNotExist:
            return Response(
                {"detail": "Meet not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is in members list
        if request.user not in meet.members.all():
            return Response(
                {"detail": "You are not a member of this meeting."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = request.user.id
        expires_in = settings.AGORA_TOKEN_EXPIRES_IN or 3600

        token = generate_meet_token(channel_name, user_id, expires_in)

        return Response(
            {"token": token, "expires_in": expires_in}, status=status.HTTP_201_CREATED
        )


class MeetCalendarView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeetCalendarSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MeetFilter

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start_datetime",
                location=OpenApiParameter.QUERY,
                description="Filter meets by start datetime (ISO format)",
                required=False,
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="end_datetime",
                location=OpenApiParameter.QUERY,
                description="Filter meets by end datetime (ISO format)",
                required=False,
                type=OpenApiTypes.DATETIME,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        return (
            Meet.objects.filter(members=user)
            .select_related("appointment")
            .prefetch_related("members")
        )
