from .models import Meet
from django_filters import rest_framework as filters


class MeetFilter(filters.FilterSet):
    start_datetime = filters.IsoDateTimeFilter(
        field_name="appointment__scheduled_start_time", lookup_expr="gte"
    )
    end_datetime = filters.IsoDateTimeFilter(
        field_name="appointment__scheduled_end_time", lookup_expr="lte"
    )

    class Meta:
        model = Meet
        fields = ["start_datetime", "end_datetime"]
