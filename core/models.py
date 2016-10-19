from datetime import datetime

from colorful.fields import RGBColorField
from django.conf import settings
from django.db import models

from core.algorithms import merge_overlapping_spans
from core.constants import palette


class TimeSpanQuerySet(models.QuerySet):
    def merged_total(self):
        """
        TimeSpans sometimes overlap. Treat overlapping spans as one continuous TimeSpan.
        Calculate the sum of such merged spans, in seconds.
        """
        merged = merge_overlapping_spans(
            (ts.start.timestamp(), ts.get_end().timestamp()) for ts in self)
        return sum(b - a for a, b in merged)

    def summed(self):
        return int(sum(ts.get_end().timestamp() - ts.start.timestamp() for ts in self))

    def focus_factor(self):
        merged_total = self.merged_total()
        if not merged_total:
            return 0
        return self.filter(bucket__type=Bucket.FOCUSED).summed() / merged_total


class TimeSpan(models.Model):
    """Represents time delimited by `start` and `end` spent on `bucket`, paid by `bucket__client`
    (or at least attributed to, money isn't always involved).

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
    bucket = models.ForeignKey('Bucket')
    day = models.ForeignKey('Day')
    # Well, TextField and max_length problem is gone
    comment = models.CharField(max_length=1024 * 100, null=True, blank=True)

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
        self.bucket.last_started = self.start
        self.bucket.save()
        super().save(*args, **kwargs)


class Bucket(models.Model):
    """
    Sums time spans. May be a task, a routine, generic activity.
    """
    FOCUSED = 'focused'
    OTHER = 'other'
    TYPES = (
        (FOCUSED, 'Focused'),
        (OTHER, 'Other'),
    )

    # short name, useful for command line identification
    tag = models.CharField(max_length=12, unique=True)
    title = models.CharField(max_length=128)
    # front-end may use this to allow links as titles
    url = models.URLField(null=True, blank=True)
    # in hours or whatever you like, will be used to set alarms, now purely informational
    estimate = models.IntegerField(null=True, blank=True)
    color = RGBColorField(colors=palette)
    # for simplicity of obtaining recent buckets, filled on TimeSpan.save
    last_started = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=TYPES, default=FOCUSED, blank=True)
    client = models.ForeignKey('Client', null=True, blank=True)

    def __str__(self):
        return '%s: %s' % (self.tag, self.title)

    def total(self):
        """
        Sum of all time_spans in seconds. Does not deal with overlaps.
        """
        return int(sum(
            ts.get_end().timestamp() - ts.start.timestamp() for ts in self.timespan_set.all()
        ))

    @classmethod
    def recent(cls):
        """List buckets recently worked on, "recent" defined in settings."""
        return cls.objects.order_by('-last_started')[:settings.RECENT_DAYS]


class Client(models.Model):
    """
    Contains buckets. Client isn't the best name, sometimes client is your employer, sometime you
    are your own client.
    """
    name = models.CharField(max_length=64, unique=True)
    code = models.CharField(max_length=4, unique=True)

    def __str__(self):
        return '{self.name} ({self.code})'.format(self=self)


class Day(models.Model):
    """
    Represents a working day. Every time span needs a Day for storing time worked that day and to
    find out the working hours to calculate time worked so far (this month). Yes, this seems
    wasteful, in most scenarios working hours will be the same every day, in some other even hours
    worked that day will be identical, but in such boring scenarios, do you need this app at all?

    FIXME: when work_* are undefined, js barks
    """
    date = models.DateField(unique=True)
    # start, end defaults are bad, make sure to reset to the same value for saturday and sundays
    work_starts = models.TimeField(default='09:00', null=True, blank=True)
    work_ends = models.TimeField(default='17:00', null=True, blank=True)

    def planned_delta(self):
        # FIXME: name, not a delta, delta value in seconds
        if not self.work_starts or not self.work_ends:
            return 0
        v = datetime.combine(
            datetime.today(), self.work_ends) - datetime.combine(datetime.today(), self.work_starts)
        return v.total_seconds()

    def focus_factor(self):
        return self.timespan_set.focus_factor()

    def __str__(self):
        return '{:%Y-%m-%d}'.format(self.date)


class Comment(models.Model):
    """Loose comment, as opposed to time_span comment.
    This isn't finished.
    """
    when = models.DateTimeField()
    text = models.TextField()
