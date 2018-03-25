"""
I didn't write tests initially, there was no need to.
I slowly start to need them but mainly for inisight module.
"""
from datetime import date, datetime
from pprint import pprint

from django.test import Client, TestCase
from django.urls import reverse

from core.models import Bucket, DailyTarget, DayCache, TimeSpan

# factories


def ts(day, hour, bucket):
    return TimeSpan(
        start=datetime(2016, 1, day, hour),
        end=datetime(2016, 1, day, hour + 1),
        bucket=bucket
    )


class InsightTests(TestCase):
    def test_test(self):
        """Start two targets, do some work on one. Next day, do some on the second. Third, on first
        and expect that it gets counted."""
        b1 = Bucket.objects.create(title='one')
        b2 = Bucket.objects.create(title='two')
        DailyTarget.objects.create(date=date(2016, 1, 1), bucket=b1, amount=7200)
        DailyTarget.objects.create(date=date(2016, 1, 1), bucket=b2, amount=7200)
        TimeSpan.objects.bulk_create([
            ts(1, 10, b1),
            ts(1, 12, b2),
            ts(2, 10, b2),
            ts(3, 10, b1),
            ts(4, 10, b1),
        ])
        DayCache.recalculate_all()
        c = Client()
        response = c.get(reverse('insight', kwargs={'start': '2016-01-01', 'end': '2016-01-03'}))
        data = response.json()
        pprint(data)
        assert '2016-01-03' in data
        id1 = str(b1.id)
        assert id1 in data['2016-01-03']
        assert not data['2016-01-02'][id1]['display']
        assert data['2016-01-03'][id1]['done_cumulative'] == 7200
        assert data['2016-01-03'][id1]['display']
