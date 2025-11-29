import math

import pytest

from shared.irt import (
    item_information_batch,
    select_next_by_information,
    mle_theta_fisher,
    eap_theta,
)


def test_batch_and_select():
    theta = 0.0
    items = [
        {"id": 1, "a": 1.0, "b": -1.0, "c": 0.2},
        {"id": 2, "a": 1.5, "b": 0.0, "c": 0.2},  # likely higher info near theta=0
        {"id": 3, "a": 0.5, "b": 1.0, "c": 0.2},
    ]
    infos = item_information_batch(theta, items)
    assert len(infos) == 3
    # selection should return id 2 at theta=0
    chosen, info, idx = select_next_by_information(theta, items)
    assert chosen["id"] == 2
    assert info == pytest.approx(infos[1])


def test_mle_theta_fisher_converges_on_simple_case():
    # Construct an easy, symmetric case around b=0
    items = [
        {"id": 1, "a": 1.0, "b": -0.5, "c": 0.0},
        {"id": 2, "a": 1.0, "b": 0.0, "c": 0.0},
        {"id": 3, "a": 1.0, "b": 0.5, "c": 0.0},
    ]
    # Simulate responses consistent with theta ~ 0.3
    theta_true = 0.3
    responses = []
    for it in items:
        # Use probability rounding to generate a deterministic pseudo-response
        from shared.irt import irf_3pl

        p = irf_3pl(theta_true, it["a"], it["b"], it.get("c", 0.0))
        responses.append(int(p >= 0.5))

    est = mle_theta_fisher(items, responses, initial_theta=0.0, max_iter=50)
    assert -2.0 < est < 2.0


def test_eap_theta_behaves_and_within_bounds():
    items = [
        {"id": 1, "a": 1.2, "b": -0.5, "c": 0.2},
        {"id": 2, "a": 0.8, "b": 0.3, "c": 0.2},
        {"id": 3, "a": 1.6, "b": 0.8, "c": 0.1},
    ]
    responses = [1, 0, 1]
    est = eap_theta(items, responses, prior_mean=0.0, prior_sd=1.0)
    assert -4.0 <= est <= 4.0
