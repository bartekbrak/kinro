from datetime import timedelta


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
