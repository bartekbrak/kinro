from django.utils.timezone import now


def merge_overlapping_spans(spans):
    """When dealing with overlapping time spans, calculate total time spent treating overlapping
    periods as one. For example:
    I've been coding at the office since 10:30 until 11:48. (78 minutes)
    But really, at 11:30 we started lunch and discussion which lasted till 12:15. (45 minutes)
    Then I went home to have a siesta. I have worked for 105 minutes, not 123.

    Takes in iterable of timestamp pairs. End falls back to now.
    """
    # willfully consume a possible generator
    _now = now()
    sorted_spans = sorted((start.timestamp(), (end or _now).timestamp()) for start, end in spans)
    if not sorted_spans:
        return []
    stack = [sorted_spans.pop(0)]
    try:
        while True:
            cur_start, cur_end = sorted_spans.pop(0)
            pre_start, pre_end = stack[-1]
            if pre_end < cur_start:
                stack.append((cur_start, cur_end))
            else:
                if pre_end < cur_end:
                    stack[-1] = pre_start, cur_end
    except IndexError:
        return stack
