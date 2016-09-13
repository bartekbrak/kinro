import re
from datetime import datetime

from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date

from core.models import Bucket, Day, TimeSpan
from core.utils import mean, to_human_readable_in_hours


def time_span_list(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    assert start and end, 'missing GET params'
    # those fitting start-end and those in progress
    queryset = TimeSpan.objects.filter(
        Q(start__gte=start, end__lte=end) | Q(start__gte=start, end__isnull=True)
    )
    data = [
        {
            'start': instance.start,
            'end': instance.get_end(),
            'title': instance.bucket.title,
            'color': instance.bucket.color,
            'rendering': 'background' if instance.bucket.type == Bucket.OTHER else '',
        } for instance in queryset
    ]
    return JsonResponse(data, safe=False)


def day_span_list(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    assert start and end, 'missing GET params'
    queryset = Day.objects.filter(date__gte=start, date__lte=end)
    data = [
        {
            'start': datetime.combine(
                instance.date, instance.work_starts) if instance.work_starts else '',
            'end': datetime.combine(
                instance.date, instance.work_ends) if instance.work_ends else '',
            'color': '#eee',
            'rendering': 'background',
            'className': 'days',
        } for instance in queryset
    ]
    return JsonResponse(data, safe=False)


def dashboard(request):
    return render(request, 'core/dashboard.html', {
        'running': TimeSpan.objects.filter(end__isnull=True),
        'recent': Bucket.recent(),
    })


def start_time_span(request, tag):
    bucket = Bucket.objects.get(tag=tag)
    in_progress = TimeSpan.objects.filter(end__isnull=True, bucket__type=Bucket.FOCUSED).count()
    assert not in_progress, 'a task is in progress'
    day, _ = Day.objects.get_or_create(date=datetime.now().date())
    TimeSpan.objects.create(start=datetime.now(), bucket=bucket, day=day)
    return HttpResponse('ok')


def end_time_span(request, tag):
    kwargs = {}
    qs = TimeSpan.objects.all()
    if tag:
        qs = qs.filter(bucket__tag=tag)
    else:
        qs = qs.filter(bucket__type=Bucket.FOCUSED)

    open_span = qs.get(end__isnull=True, **kwargs)
    open_span.end = datetime.now()
    open_span.save()
    return HttpResponse('ok')


def window(year, month, start_day, end_day):
    """
    windows provides an insight into your data, it allows to calculate the interesting bits over a
    period of time.

    This code is  not mature, it does the job but isn't very customizable or clean, I really
    couldn't care less at this stage. Stop fantasizing. No, you.

    To calculate progressive totals we need some highest unit of time denoting the start point of
    that calculation. I choose a month.
    """
    start = parse_date(start_day)
    end = parse_date(end_day)
    days = Day.objects.filter(date__year=year, date__month=month).order_by('date')
    planned_so_far = 0
    worked_so_far = 0
    ff_so_far = 0
    result = []
    for i, day in enumerate(days):
        planned_so_far += day.planned_delta()
        worked = day.timespan_set.merged_total()
        worked_so_far += worked
        balance = to_human_readable_in_hours(worked_so_far - planned_so_far)
        ff = day.focus_factor() * 100
        ff_so_far += ff
        result.append({
            'date': day.date,
            'display': '%s (%s) f:%.2f' % (to_human_readable_in_hours(worked), balance, ff),
            'balance': balance,
            'enough': worked_so_far > planned_so_far,
            'worked': {
                'so_far': to_human_readable_in_hours(worked_so_far),
                'today': to_human_readable_in_hours(worked),
            },
            'planned': {
                'so_far': to_human_readable_in_hours(planned_so_far),
                'today': to_human_readable_in_hours(day.planned_delta()),
            },
            'focus_factor': {
                'progressive_mean': mean([d.focus_factor() * 100 for d in days[:i + 1]]),
                'today': ff
            },
        })
    return [v for v in result if (start <= v['date'] <= end)]


def insight(request, start, end):
    # move all this logic to "Month" and stop calling it month
    months = set()
    years = set()
    for one_date in (start, end):
        m = re.search('(?P<year>\d{4})-(?P<month>\d{1,2})-\d{1,2}', one_date)
        months.add(m.groupdict()['month'])
        years.add(m.groupdict()['year'])
    year = years.pop()
    windows = []
    for month in months:
        windows += window(year, month, start, end)
    return JsonResponse(windows, safe=False)


def fake_comments(request):
    # List fake_comments, Work in progress
    fake = [
        {
            "start": "2016-09-15T09:00:00",
            "end": "2016-09-15T09:10:00",
            "title": 'fake comment, fake comment, fake comment, fake comment, fake comment,  '
        }
    ]
    return JsonResponse(fake, safe=False)
