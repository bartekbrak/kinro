def merge_overlapping_spans(spans):
    """When dealing with overlapping time spans, calculate total time spent treating overlapping
    periods as one. For example:
    I've been coding at the office since 10:30 until 11:48. (78 minutes)
    But really, at 11:30 we started lunch and discussion which lasted till 12:15. (45 minutes)
    Then I went home to have a siesta. I have worked for 105 minutes, not 123.
    """
    # willfully consume a possible generator
    sorted_spans = sorted(spans)
    if not sorted_spans:
        return []
    stack = [sorted_spans.pop(0)]
    try:
        while True:
            cur = sorted_spans.pop(0)
            if stack[-1][1] < cur[0]:
                stack.append(cur)
            else:
                if stack[-1][1] < cur[1]:
                    stack[-1] = stack[-1][0], cur[1]
    except IndexError:
        return stack
