from apps.seedtest_api.services.scoring import (
    raw_to_scaled,
    theta_to_percentile,
    theta_to_scaled,
)


def test_theta_to_scaled_clipping_and_linear():
    assert theta_to_scaled(0.0) == 100
    assert theta_to_scaled(1.0) == 150
    assert theta_to_scaled(-1.0) == 50
    # clip bounds
    assert theta_to_scaled(10.0) == 200
    assert theta_to_scaled(-10.0) == 0


def test_theta_to_percentile_monotonic_bounds():
    assert 0 <= theta_to_percentile(-5.0) <= 5
    assert 45 <= theta_to_percentile(-0.125) <= 55
    assert 95 <= theta_to_percentile(1.64) <= 100


def test_raw_to_scaled_linear():
    assert raw_to_scaled(0, 10) == 0
    assert raw_to_scaled(5, 10) in (100, 101)  # rounding
    assert raw_to_scaled(10, 10) == 200
    # defensive
    assert raw_to_scaled(1, 0) == 0
