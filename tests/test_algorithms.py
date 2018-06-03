from unittest.mock import patch

import pytest

from _datetime import datetime
from core.algorithms import merge_overlapping_spans


def t(start, end):
    return datetime.fromtimestamp(start), datetime.fromtimestamp(end) if end else None


@pytest.mark.parametrize('spans, expected', (
    ([t(4, 7), t(1, 2), t(5, 9), t(6, 6)], [(1, 2), (4, 9)]),
    ([t(-10, -5), t(-11, 2), t(4, 5)], [(-11, 2), (4, 5)]),
))
def test_merge_overlapping_spans(spans, expected):
    assert merge_overlapping_spans(spans) == expected


@patch('core.algorithms.now', return_value=datetime.fromtimestamp(5))
def test_merge_overlapping_spans_no_end(mocked):
    spans = t(-10, -5), t(-11, 2), t(4, None)
    expected = [(-11, 2), (4, 5)]
    assert merge_overlapping_spans(spans) == expected
    assert mocked.call_count == 1
