import json
import logging
from base64 import b64encode
from datetime import timedelta
from http.client import HTTPSConnection
from random import randint

from django.utils.safestring import mark_safe

log = logging.getLogger('general')


def pairwise(iterable):
    """s -> (s0, s1), (s2, s3), (s4, s5), ..."""
    a = iter(iterable)
    return zip(a, a)


def to_human_readable(seconds):
    """
    * negative time not supported.

    In : to_human_readable(213321)
    Out: '2 days, 11:15:21 (3555 minutes)'

    """
    assert seconds > 0, 'Negative time makes no sense to me.'
    return '%s (%.f minutes)' % (str(timedelta(seconds=seconds)), seconds / 60)


def to_human_readable_in_hours(seconds):
    """
    * Seconds are not displayed.
    * Negative time supported.

    In : to_human_readable_in_hours(1)
    Out: '0:00'

    In : to_human_readable_in_hours(100)
    Out: '0:01'

    In : to_human_readable_in_hours(213321)
    Out: '59:15'

    In : to_human_readable_in_hours(-2000)
    Out: '-0:33'

    """
    sign = ''
    if seconds < 0:
        sign = '-'
        seconds = abs(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%s%d:%02d" % (sign, h, m)

def to_human_readable_in_hours_jira(seconds):
    sign = ''
    if seconds < 0:
        sign = '-'
        seconds = abs(seconds)
    return "%s%02d" % (sign, seconds / 60 / 60)

def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


def make_list_unique(seq):
    """
    >>> make_list_unique([1, 1, 2, 1, 2, 2, 4, 0, 4])
    [1, 2, 4, 0]
    """
    # http://stackoverflow.com/a/480227/1472229
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def contrasting_text_color(hex_str):
    # http://stackoverflow.com/a/37603471/1472229
    # http://codepen.io/WebSeed/full/pvgqEq/
    # there's a copy of this in frontend
    if hex_str.startswith('#'):
        hex_str = hex_str[1:]
    r, g, b = hex_str[:2], hex_str[2:4], hex_str[4:]
    if 1 - (int(r, 16) * 0.299 + int(g, 16) * 0.587 + int(b, 16) * 0.114) / 255 < 0.5:
        return 'black'
    else:
        return 'white'


def draw_progress_bar(done, planned, label='', bg_color='#a9a9a9', extra_css=''):
    # in seconds, dude
    if planned == 0 and done == 0:
        progress = 0
    else:
        progress = done / planned * 100
    balance = done - planned
    label = '%i%% %s' % (progress, label)
    capped_progress = 100 if progress > 100 else progress
    hover = '{done} of {planned} ({sign}{balance})'.format(
        done=to_human_readable_in_hours(int(done)),
        planned=to_human_readable_in_hours(int(planned)),
        sign='+' if balance > 0 else '',
        balance=to_human_readable_in_hours(int(balance)),
    )
    color = contrasting_text_color(bg_color)
    return mark_safe('''
    <div class="progress" style="{extra_css}" title="{hover}">
        <div class="progress_label" style="color:{color}">{label}</div>
        <div class="progress_bar" style="width:{width}%; background-color:{bg_color}"></div>
      </div>
    '''.format(
        label=label, width=capped_progress, hover=hover, bg_color=bg_color,
        color=color, extra_css=extra_css))


def date_range(from_date, to_date):
    return [from_date + timedelta(days=d) for d in range(0, (to_date-from_date).days + 1)]


def random_color():
    return '#%02X%02X%02X' % (randint(0, 255), randint(0, 255), randint(0, 255))


def bucket_from_jira(task_no: str, parent: int, url: str, auth: str):
    """
    create bucket from jira, sample:
    bucket_from_jira('RB-10', 220, 'jira.softheart.io', 'bartek.rychlicki:________')
    """
    assert 'http' not in url
    c = HTTPSConnection(url)
    c.request(
        'GET',
        '/rest/api/latest/issue/%s' % task_no,
        headers={
            'Authorization': 'Basic %s' % b64encode(auth).decode("ascii")
        }
    )
    data = json.loads(c.getresponse().read().decode('utf-8'))
    from core.models import Bucket
    return Bucket.objects.create(
        parent=Bucket.objects.get(pk=parent),
        title='%s: %s' % (task_no, data['fields']['summary']),
        url='https://%s/browse/%s' % (url, task_no),
        type=Bucket.FOCUSED
    )
