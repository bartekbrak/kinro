import json
from datetime import datetime, timedelta

from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from core.algorithms import merge_overlapping_spans
from core.fields import ColorField
from core.utils import contrasting_text_color, date_range


class TimeSpanQuerySet(models.QuerySet):
    def merged_total(self):
        """
        TimeSpans sometimes overlap. Treat overlapping spans as one continuous TimeSpan.
        Calculate the sum of such merged spans, in seconds.

        return: seconds
        """
        merged = merge_overlapping_spans(
            (ts.start.timestamp(), ts.get_end().timestamp()) for ts in self)
        return sum(b - a for a, b in merged)

    def focus_factor(self):
        # The idea is useful but I just need to think how to display it nicely after recent changes
        raise DeprecationWarning
        # merged_total = self.merged_total()
        # if not merged_total:
        #     return 0
        # return self.filter(bucket__type=Bucket.FOCUSED).merged_total() / merged_total


class TimeSpan(models.Model):
    """Represents time delimited by `start` and `end` spent on a given `bucket`.

    Can be either:
    a] focused - no two of such kind can exist at a point in time or, in other words focused time
       spans cannot overlap.
       You can't do two things at once, can you? Some checks will be enforced.
    b] other - no restrictions, anything you want to measure, can overlap. The initial intention was
       to have a background "task" payable to your main client, a fallback bucket for breaks,
       toilet, lunches or general faffing around. Such task represents time that you feel you should
       be paid for but you don't care to measure into any specific bucket.
    The above distinction affects how overlapping time will be treated in calculating totals. The
    fact that "other" can overlap with a "focused" time span allows subtracting which translates
    into real life like so, for example: - You come to work at 10:00 and Leave at 16:12, whatever
    happens during that time will be billed to client X, except that one time when you helped a
    colleague for 45 minutes, that should be subtracted and paid from a different "budget".
    Initially this model mimicked slightly Event Object from [Event_Object]. Eventually, only most
    generic fields stayed on.

    I decided not to allow much visual customisation on the level of time span, like background and
    text color, these are inherited from the bucket. This is, however supported by the front end
    renderer, should oyu decide to go other way.

    [Event_Object] http://fullcalendar.io/docs/event_data/Event_Object/
    """
    # Now that we link against a day, is TimeField would be better than DateTimeField
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    bucket = TreeForeignKey('Bucket')
    comment = models.TextField(null=True, blank=True)

    objects = TimeSpanQuerySet.as_manager()

    class Meta:
        ordering = ('-start',)

    def __str__(self):
        # FIXME: move to admin.py, it's the only place that uses this
        f = '%H:%M'
        return '%s__%s-%s' % (
            self.start.strftime('%Y.%m.%d'),
            self.start.strftime(f),
            self.end.strftime(f) if self.end else '?',
        )

    def get_end(self):
        """If the span hasn't finished, for calculations' reasons, pretend it's finished now."""
        return self.end or datetime.now()

    def save(self, *args, **kwargs):
        # FIXME: check if delta does not span over midnight - one day only
        # sets bucket.last_started
        self.bucket.save()
        super().save(*args, **kwargs)
        DayCache.recalculate(self.start.date())

    def delete(self, using=None, keep_parents=False):
        ret = super().delete(using, keep_parents)
        DayCache.recalculate(self.start.date())
        return ret


class Bucket(MPTTModel):
    """
    Sums time spans. May be a task, a routine, generic activity.
    """
    FOCUSED = 'focused'
    CLIENTS = 'client'
    TYPES = (
        (FOCUSED, 'Focused'),
        (CLIENTS, 'Client'),
    )
    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children',
        db_index=True, on_delete=models.PROTECT)
    # short name, useful for command line identification
    title = models.CharField(max_length=128)
    # front-end may use this to allow links as titles
    url = models.URLField(null=True, blank=True)
    # in hours or whatever you like, might be used to set alarms, currently purely informational
    # FIXME: decimals, how to 4.5hrs here?
    estimate = models.FloatField(null=True, blank=True)
    color = ColorField(max_length=7)
    # for simplicity of obtaining recent buckets, filled on TimeSpan.save
    last_started = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=10, choices=TYPES, default=FOCUSED, blank=True)

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title

    def family_time_spans_q(self):
        """Returns queryset of all timespans in this bucket and its descendant buckets."""
        # FIXME: do simple query if it's a leaf
        family_ids = self.get_descendants(include_self=True).values_list('id', flat=True)
        return TimeSpan.objects.filter(bucket__in=family_ids)

    def done(self, date):
        """How much time was spent in this bucket on a given date?"""
        return self.family_time_spans_q().filter(
            start__date=date
        ).merged_total()

    @property
    def text_color(self):
        return contrasting_text_color(self.color)


class DailyTarget(models.Model):
    """Your ambition for the day. Like:
     - I plan to work for 8 hours.
     - I also plan to also study (spend time on Bucket 11 - Learn Portuguese) for 45 minutes.
     - I plan to do something with any of my projects for 2hrs - choose a Bucket that collects
       other buckets.
     """
    date = models.DateField(null=True)
    bucket = TreeForeignKey('Bucket', on_delete=models.PROTECT)
    amount = models.PositiveIntegerField()
    fresh_start = models.BooleanField(default=False)

    class Meta:
        unique_together = ('date', 'bucket')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        DayCache.recalculate(self.date)


class DayCache(models.Model):
    """Insight mechanism calculates cumulative progress of DailyTarget objects and relevant TimeSpan
    totals. These calculations are expensive and change little for the past days. This model stores
    data used by Insight and displayed by Insight front-end.

    cached data is serialized as json, JsonField was not used as the data will never and ought not
    to be used in lookups.

    WARNING: JSON
    """

    date = models.DateField()
    previous = models.OneToOneField('self', null=True, blank=True, related_name='next')
    data_json = models.TextField()

    _data = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self.data_json = json.dumps(value)

    @data.getter
    def data(self):
        if not self._data:
            # JSON does not allow integers as keys but I rally like them
            self._data = {int(k): v for k, v in json.loads(self.data_json).items()}
        return self._data

    @classmethod
    def invalidate(cls, since):
        """Delete from `since` to now. Recalculate and save."""
        DayCache.objects.filter(date__gte=since).delete()

    @classmethod
    def recalculate_all(cls):
        cls.recalculate(DailyTarget.objects.all().order_by('date').first().date)

    @classmethod
    def recalculate(cls, since):
        # FIXME: hardly readable, clean up
        cls.invalidate(since)
        previous = cls.objects.order_by('date').last()
        print('previous', previous)
        all_dts = DailyTarget.objects.all().order_by('date')
        if not all_dts:
            return
        latest_target = all_dts.last().date
        last_span = TimeSpan.objects.order_by('start').last().start.date()
        latest = max(latest_target, last_span)
        targets_index = {}
        for dt in DailyTarget.objects.filter(date__gte=since):
            targets_index.setdefault(dt.date, {})
            targets_index[dt.date][dt.bucket.id] = dt

        for a_date in date_range(since, latest):
            print(a_date)
            this_day = {}
            if a_date in targets_index:
                for target in targets_index[a_date].values():
                    bucket = target.bucket
                    done = bucket.done(a_date)
                    if previous:
                        for i, j in previous.data.items():
                            print('previous.data', i, j)
                    if previous and not target.fresh_start and bucket.id in previous.data:
                        pb = previous.data[bucket.id]
                        done_cumulative = pb['done_cumulative'] + done
                        planned_cumulative = pb['planned_cumulative'] + target.amount
                    else:
                        done_cumulative = done
                        planned_cumulative = target.amount

                    this_day[bucket.id] = {
                        'display': True,
                        'color': bucket.color,
                        'title': bucket.title,
                        'done': done,
                        'done_cumulative': done_cumulative,
                        'planned': target.amount,
                        'planned_cumulative': planned_cumulative,
                        # Concerns this day only
                        # FIXME: batter name or mechanism needed
                        'local': True
                    }

            # Maybe there is work which was not targeted that day but does add to previous
            # unfinished targets ?
            # This only makes sense when there are previous targets.
            if previous:
                unfinished_targets = set(previous.data.keys()) - set(this_day.keys())

                for bucket_id in unfinished_targets:
                    pb = previous.data[bucket_id]
                    bucket = Bucket.objects.get(id=bucket_id)
                    done_today = bucket.done(a_date)
                    done_cumulative = done_today + pb['done_cumulative']
                    planned_cumulative = pb['planned_cumulative']
                    # Drop tracking targets that were finished.
                    was_not_finished_yesterday = pb['done_cumulative'] < pb['planned_cumulative']
                    # was_not_finished_today = done_cumulative < planned_cumulative
                    worked_on_it_today = bool(done_today)
                    if True:
                        # Yes, carry on the log for the future use
                        this_day[bucket_id] = {
                            # But only display it if work was done that day.
                            # THINK: In the future I might want to call it "verbosity".
                            'display': worked_on_it_today,
                            'color': bucket.color,
                            'title': bucket.title,
                            'done_cumulative': done_cumulative,
                            'planned_cumulative': planned_cumulative,
                        }
            if this_day:
                dc = DayCache(date=a_date, previous=previous)
                dc.data = this_day
                previous = dc
                dc.save()
