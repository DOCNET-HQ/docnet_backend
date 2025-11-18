from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"rooms", views.ChatRoomViewSet, basename="chatroom")
router.register(r"messages", views.MessageViewSet, basename="message")
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"invites", views.GroupInviteViewSet, basename="invite")

urlpatterns = [
    path("", include(router.urls)),
]
