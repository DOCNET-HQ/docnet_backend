from django.urls import path
from profiles.views import SpecialtyListView


urlpatterns = [
    path("specialties/", SpecialtyListView.as_view(), name="specialty-list"),
]
