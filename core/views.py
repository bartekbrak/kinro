from datetime import datetime, timedelta

import markdown
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.dateparse import parse_date

from core.models import Bucket, DayCache, TimeSpan
from core.utils import contrasting_text_color


def time_span_list(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    assert start and end, 'missing GET params'
    # those fitting start-end and those in progress
    queryset = TimeSpan.objects.filter(
        Q(start__gte=start, end__lte=end) | Q(start__gte=start, end__isnull=True)
    )
    running = TimeSpan.objects.filter(bucket__type=Bucket.FOCUSED, end__isnull=True)
    running_id = running.get().id if running else None
    data = [
        {
            'start': instance.start,
            'end': instance.get_end(),
            'title': instance.bucket.title,
            'color': instance.bucket.color,
            'textColor': contrasting_text_color(instance.bucket.color),
            'comment': markdown.markdown(instance.comment or ''),
            'url': reverse('admin:core_timespan_change', args=(instance.id, )),
            'bucket_url': reverse('admin:core_bucket_change', args=(instance.bucket.id, )),
            'rendering': 'background' if instance.bucket.type == Bucket.CLIENTS else '',
            'className': 'current_event' if instance.id == running_id else '',
        } for instance in queryset
    ]
    return JsonResponse(data, safe=False)


def dashboard(request, start=None):
    running = TimeSpan.objects.filter(end__isnull=True)
    running_focused = running.filter(bucket__type=Bucket.FOCUSED)
    running_buckets = [o.bucket for o in running]

    return render(request, 'core/dashboard.html', {
        'running': running_buckets,
        'recent': Bucket.objects.filter(
            last_started__gte=(datetime.today() - timedelta(days=settings.RECENT_DAYS)),
        ).exclude(
            id__in=[_.id for _ in running_buckets]
        ).order_by('-last_started'),
        'defaultDate': "'%s'" % start if start else 'null',
        'title': running_focused.get().bucket.title if running_focused else ''
    })


def toggle(request, title):
    running = TimeSpan.objects.filter(bucket__title=title, end__isnull=True)
    if running:
        return end_time_span(request, title)
    else:
        return start_time_span(request, title)


def start_time_span(request, title):
    bucket = Bucket.objects.get(title=title)
    if TimeSpan.objects.filter(end__isnull=True, bucket__type=Bucket.FOCUSED).count():
        return HttpResponse("focused task already in progress, can't have two", status=400)
    TimeSpan.objects.create(start=datetime.now(), bucket=bucket)
    return HttpResponse('ok')


def end_time_span(request, title):
    # FIXME: call it end_focused_task
    if title:
        open_span = TimeSpan.objects.filter(bucket__title=title).get(end__isnull=True)
    else:
        # or close latest focused
        open_span = TimeSpan.objects.filter(bucket__type=Bucket.FOCUSED).get(end__isnull=True)
    open_span.end = datetime.now()
    open_span.save()
    return HttpResponse('ok')


def insight(request, start, end):
    # FIXME: dirty hack, recalculate today so that  progress bars show truth
    # Fix by treating today differently, skip cache
    DayCache.recalculate(datetime.today().date())

    return JsonResponse(data={
        str(o.date): o.data
        for o in DayCache.objects.filter(date__gte=parse_date(start), date__lte=parse_date(end))
    }, safe=False)


def tree(request):
    return render(request, 'core/tree.html')
