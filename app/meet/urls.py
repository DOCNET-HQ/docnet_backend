from django.urls import path
from . import views

urlpatterns = [
    path("token/", views.MeetTokenCreateView.as_view(), name="meet-token-create"),
    path("calendar/", views.MeetCalendarView.as_view(), name="meet-calendar-list"),
    path("<str:meet_id>/", views.MeetDetailView.as_view(), name="meet-detail"),
]
