from rest_framework import serializers
from .models import AIModel, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class AIModelSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = AIModel
        fields = [
            'id', 'title', 'description', 'version', 'model_type', 'status',
            'tags', 'icon_name', 'image_url', 'model_url', 'docs_url',
            'document_url', 'enabled', 'created_at'
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_document_url(self, obj):
        if obj.document:
            return obj.document.url
        return None


class AIModelListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AIModel
        fields = [
            'id', 'title', 'description', 'version', 'model_type', 'status',
            'tags', 'icon_name', 'image_url', 'model_url', 'docs_url', 'enabled'
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
