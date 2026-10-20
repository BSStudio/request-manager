from datetime import datetime, time

from django.utils.timezone import localdate, make_aware
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from api.v1.admin.reports.serializers import (
    ReportAdminQuerySerializer,
    ReportAdminSerializer,
)
from common.rest_framework.permissions import IsStaffUser
from video_requests.models import Request, Video


class ReportAdminView(APIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        parameters=[ReportAdminQuerySerializer], responses=ReportAdminSerializer
    )
    def get(self, request):
        query = ReportAdminQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        date_after = query.validated_data["date_after"]
        date_before = query.validated_data["date_before"]

        # An event belongs to every day it runs on, so one spanning two months
        # is in both reports. One that ends at midnight does not run on the next day.
        requests = (
            Request.objects.filter(
                start_datetime__date__lte=date_before,
                end_datetime__gt=make_aware(datetime.combine(date_after, time.min)),
            )
            .exclude(
                status__in=[
                    Request.Statuses.DENIED,
                    Request.Statuses.CANCELED,
                    Request.Statuses.FAILED,
                ]
            )
            .order_by("start_datetime", "title")
        )
        videos = Video.objects.filter(
            edited_at__range=[date_after, date_before]
        ).order_by("edited_at", "title")

        return Response(
            ReportAdminSerializer(
                {
                    "requests": [
                        {
                            "date": localdate(req.start_datetime),
                            "id": req.id,
                            "title": req.title,
                        }
                        for req in requests
                    ],
                    "videos": [
                        {"date": video.edited_at, "id": video.id, "title": video.title}
                        for video in videos
                    ],
                }
            ).data
        )
