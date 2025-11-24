import django_filters
from django.db import models
from .models import AIModel


class AIModelFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    model_type = django_filters.ChoiceFilter(choices=AIModel.ModelType.choices)
    status = django_filters.ChoiceFilter(choices=AIModel.ModelStatus.choices)
    tags = django_filters.CharFilter(method='filter_tags')

    class Meta:
        model = AIModel
        fields = ['search', 'model_type', 'status', 'tags']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value) |
            models.Q(tags__name__icontains=value)
        ).distinct()

    def filter_tags(self, queryset, name, value):
        tag_names = [tag.strip() for tag in value.split(',')]
        return queryset.filter(tags__name__in=tag_names).distinct()
