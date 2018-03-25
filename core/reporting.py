"""
primitive reporing for shell_plus
- TODO: split into data and formatters
- TODO: describe
- TODO: dry
"""
from datetime import datetime

from core.models import Bucket
from core.utils import to_human_readable_in_hours as human
from collections import defaultdict


def report_a_day(day=datetime.today().strftime('%Y-%m-%d'), split_names=('food', )):
    # softheart (current employer) rules
    print('-' * 60)
    data = defaultdict(lambda: defaultdict(int))
    for bucket in Bucket.objects.filter(timespan__start__date=day).distinct():
        client = (
            Bucket.objects.get(id=bucket.id).get_ancestors().filter(type='client').get().title
            if bucket.type != Bucket.CLIENTS
            else bucket.title
        )
        seconds = bucket.done(day)
        # if bucket.type == Bucket.CLIENTS:
        #     data[client]['all'] += seconds
        if bucket.url:
            data[client]['task'] += seconds
            data[client][(bucket.id, bucket.url, bucket.title)] += seconds
        else:
            if bucket.type == Bucket.CLIENTS:
                data[client]['all'] += seconds
            else:
                data[client][(bucket.id, 'url not specified', bucket.title)] += seconds
        hr = human(seconds)
        print('%4.4s %-6.6s %40.40s : %-60.60s' % (bucket.id, hr, bucket.url, bucket.title))
    for client, seconds in data.items():
        non_task = seconds['all'] - seconds['task']
        print(
            '%s\r\t %s  -- all(%s) - tasks(%s) = %s ' % (
                '-' * 60,
                client,
                human(seconds['all']),
                human(seconds['task']),
                human(non_task)
            )
        )
        only_tasks = {k: v for k, v in seconds.items() if k not in ('all', 'task') and k[1] != 'url not specified'}
        per_task = non_task / len(only_tasks)
        print('each got +%s' % human(per_task))
        for (bucket_id, bucket_url, bucket_title), task_seconds in only_tasks.items():
            hr = human(task_seconds + per_task)
            print('%4.4s %-6.6s %40.40s : %-60.60s' % (bucket_id, hr, bucket_url, bucket_title))


def report_month(year, month):
    # clean this
    cache = {}
    client_generic = defaultdict(int)
    for bucket in Bucket.objects.filter(
        timespan__start__date__year=year,
        timespan__start__date__month=month,
    ).distinct():
        seconds = bucket.family_time_spans_q().filter(
            start__date__year=year,
            start__date__month=month,
        ).merged_total()
        if bucket.type == 'client':
            client_generic[bucket.title] += seconds
        if bucket.url:
            client_title = cache.setdefault(bucket.id, Bucket.objects.get(id=bucket.id).get_ancestors().filter(type='client').get().title)
            client_generic[client_title] -= seconds
        hr = human(seconds)
        print('%4.4s %-6.6s %40.40s : %-60.60s' % (bucket.id, hr, bucket.url, bucket.title))
    for client, cumulative in client_generic.items():
        if cumulative > 0:
            print(client, human(cumulative))
