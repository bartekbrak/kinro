"""
I didn't write tests initially, there was no need to.
I slowly start to need them but mainly for inisight module.
"""
from datetime import date, datetime
from pprint import pprint

from dateutil.parser import parse as d
from django.test import Client
from django.urls import reverse
from freezegun import freeze_time

from core.factories import TimeSpanFactory
from core.models import Bucket, DailyTarget, DayCache, TimeSpan

# factories
FIVE_HOURS = 18000
HOUR_AND_A_HALF = 5400
TWO_H = 7200
ONE_HOUR = 3600


def ts(day, hour, bucket):
    return TimeSpan(
        start=datetime(2016, 1, day, hour),
        end=datetime(2016, 1, day, hour + 1),
        bucket=bucket
    )


def test_recalculate_all(db):
    """Start two targets, do some work on one. Next day, do some on the second. Third, on first
    and expect that it gets counted."""
    b1 = Bucket.objects.create(title='one')
    b2 = Bucket.objects.create(title='two')
    DailyTarget.objects.create(date=date(2016, 1, 1), bucket=b1, amount=TWO_H)
    DailyTarget.objects.create(date=date(2016, 1, 1), bucket=b2, amount=TWO_H)
    TimeSpan.objects.bulk_create([
        ts(1, 10, b1),
        ts(1, 12, b2),
        ts(2, 10, b2),
        ts(3, 10, b1),
        ts(4, 10, b1),  # won't be in the results
    ])
    DayCache.recalculate_all()
    c = Client()
    response = c.get(reverse('insight', kwargs={'start': '2016-01-01', 'end': '2016-01-03'}))
    data = response.json()
    pprint(data)
    assert list(data.keys()) == ['2016-01-01', '2016-01-02', '2016-01-03']
    id1 = str(b1.id)
    assert id1 in data['2016-01-03']
    assert not data['2016-01-02'][id1]['display']
    assert data['2016-01-03'][id1]['done_cumulative'] == TWO_H
    assert data['2016-01-03'][id1]['display']


def test_time_span_openended(db):
    ts = TimeSpanFactory(start=d('2018-01-01 10:00'), end=d('2018-01-01 11:00'))
    b = ts.bucket
    assert TimeSpan.objects.done_on_day(d('2018-01-01'), b) == ONE_HOUR
    TimeSpanFactory(start=d('2018-01-01 10:30'), end=d('2018-01-01 11:30'), bucket=b)
    assert TimeSpan.objects.done_on_day(d('2018-01-01'), b) == HOUR_AND_A_HALF
    with freeze_time(d("2018-01-01 15:00")):
        TimeSpanFactory(start=d('2018-01-01 10:30'), end=None, bucket=b)
        assert TimeSpan.objects.done_on_day(d('2018-01-01'), b) == FIVE_HOURS
