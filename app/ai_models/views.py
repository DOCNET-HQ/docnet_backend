from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from .models import AIModel
from .serializers import AIModelSerializer, AIModelListSerializer
from .filters import AIModelFilter


class StandardPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 100


class AIModelListView(generics.ListAPIView):
    serializer_class = AIModelListSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = AIModelFilter

    def get_queryset(self):
        return AIModel.objects.prefetch_related('tags').all()


class AIModelDetailView(generics.RetrieveAPIView):
    serializer_class = AIModelSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return AIModel.objects.prefetch_related('tags').all()
