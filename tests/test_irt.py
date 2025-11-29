import math
import pytest

from shared.irt import irf_3pl, item_information_3pl


def test_irf_3pl_basic_monotonicity():
    a, b, c = 1.2, 0.0, 0.2
    p_low = irf_3pl(-3.0, a, b, c)
    p_mid = irf_3pl(0.0, a, b, c)
    p_high = irf_3pl(3.0, a, b, c)
    assert c <= p_low < p_mid < p_high < 1.0


def test_irf_3pl_limits():
    a, b, c = 1.0, 0.0, 0.25
    assert irf_3pl(-1e6, a, b, c) == pytest.approx(c, rel=0, abs=1e-12)
    assert irf_3pl(+1e6, a, b, c) == pytest.approx(1.0, rel=0, abs=1e-12)


def test_irf_2pl_equivalence_when_c_zero():
    a, b, c = 1.7, 0.5, 0.0
    p = irf_3pl(0.5, a, b, c)
    # Should reduce to logistic sigmoid
    z = a * (0.5 - b)
    expected = 1.0 / (1.0 + math.exp(-z))
    assert p == pytest.approx(expected, rel=0, abs=1e-12)


def test_iif_non_negative_and_peaks_near_b():
    a, b, c = 1.2, 0.3, 0.2
    i_left = item_information_3pl(b - 1.0, a, b, c)
    i_center = item_information_3pl(b, a, b, c)
    i_right = item_information_3pl(b + 1.0, a, b, c)
    assert i_left >= 0 and i_center >= 0 and i_right >= 0
    assert i_center >= max(i_left, i_right)


def test_iif_zero_in_edge_cases():
    a, b, c = 1.0, 0.0, 0.0
    # Extreme P close to 0 or 1 should yield ~0 information due to numeric guard
    assert item_information_3pl(-1e6, a, b, c) == pytest.approx(0.0, rel=0, abs=1e-12)
    assert item_information_3pl(+1e6, a, b, c) == pytest.approx(0.0, rel=0, abs=1e-12)


def test_iif_degenerate_c_close_to_one():
    a, b, c = 1.0, 0.0, 0.999999999
    assert item_information_3pl(0.0, a, b, c) == 0.0
