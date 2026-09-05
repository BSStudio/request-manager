from django.db.models import Q
from django.forms import IntegerField
from django_filters.rest_framework import (
    DateFilter,
    DateFromToRangeFilter,
    Filter,
    FilterSet,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from common.models import User
from video_requests.models import Request, Todo, Video


class IntegerFilter(Filter):
    """
    Helper filter class to change type of value to Integer
    because NumberFilter would use Decimal type which would return empty queryset when filtering.
    """

    field_class = IntegerField


class RequestFilter(FilterSet):
    deadline = DateFromToRangeFilter()
    start_datetime = DateFromToRangeFilter()
    status = MultipleChoiceFilter(choices=Request.Statuses.choices)


class TodoFilter(FilterSet):
    assignees = extend_schema_field(OpenApiTypes.INT)(
        ModelMultipleChoiceFilter(
            field_name="assignees__id",
            queryset=User.objects.all(),
            to_field_name="id",
        )
    )
    status = MultipleChoiceFilter(choices=Todo.Statuses.choices)


class VideoFilter(FilterSet):
    last_aired = DateFilter(method="filter_last_aired")
    length_max = extend_schema_field(OpenApiTypes.NUMBER)(
        IntegerFilter(field_name="additional_data__length", method="filter_length_max")
    )
    length_min = extend_schema_field(OpenApiTypes.NUMBER)(
        IntegerFilter(field_name="additional_data__length", lookup_expr="gte")
    )
    request_start_datetime = DateFromToRangeFilter(field_name="request__start_datetime")
    status = MultipleChoiceFilter(choices=Video.Statuses.choices)

    @staticmethod
    def filter_last_aired(queryset, name, value):
        # The video was last aired before the given date or never.
        return queryset.filter(
            Q(**{f"{name}__lte": value}) | Q(**{f"{name}__isnull": True})
        )

    @staticmethod
    def filter_length_max(queryset, name, value):
        # Length is less than given value including nulls.
        return queryset.filter(
            Q(**{f"{name}__lte": value}) | Q(**{f"{name}__isnull": True})
        )
