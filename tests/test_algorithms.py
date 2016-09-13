import pytest

from core.algorithms import merge_overlapping_spans


@pytest.mark.parametrize('a, expected', (
    ([(4, 7), (1, 2), (5, 9), (6, 6)], [(1, 2), (4, 9)]),
    ([(-10, -5), (-11, 2), (4, 5), ], [(-11, 2), (4, 5)]),
))
def test_merge_overlapping_spans(a, expected):
    assert merge_overlapping_spans(a) == expected
