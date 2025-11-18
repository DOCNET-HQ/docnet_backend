from rest_framework import generics
from profiles.models import Specialty
from profiles.serializers import SpecialtySerializer


class SpecialtyListView(generics.ListAPIView):
    """
    API view to list all specialties
    """

    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
