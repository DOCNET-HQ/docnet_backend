from profiles.models import Specialty
from rest_framework import serializers


class SpecialtySerializer(serializers.ModelSerializer):
    """
    Serializer for Specialty model
    """

    class Meta:
        model = Specialty
        fields = ["id", "name", "image", "description"]
        read_only_fields = ["id"]
