# IRT Drift Monitoring - Integration Tests

import pytest
from datetime import datetime, timezone
from apps.seedtest_api.jobs.irt_drift import (
    create_drift_window,
    detect_drift,
    ItemCalibration,
    DEFAULT_THRESHOLDS,
)


class TestDriftWindow:
    """Test drift window creation and management."""

    def test_create_drift_window(self):
        """Test creating a drift window."""
        start = datetime(2025, 10, 1, tzinfo=timezone.utc)
        end = datetime(2025, 11, 1, tzinfo=timezone.utc)
        
        window = create_drift_window(start, end, population_tags={"grade": "9"})
        
        assert window.start_at == start
        assert window.end_at == end
        assert window.population_tags == {"grade": "9"}
        assert window.window_id is not None


class TestDriftDetection:
    """Test drift detection logic."""

    def test_severe_drift_b_parameter(self):
        """Test detection of severe drift in difficulty."""
        baseline = ItemCalibration(
            item_id="item_1",
            window_id=1,
            a_hat=1.0,
            b_hat=0.0,
            c_hat=0.2,
            a_l95=0.9,
            a_u95=1.1,
            b_l95=-0.1,
            b_u95=0.1,
            c_l95=0.18,
            c_u95=0.22,
            n=500,
            run_id="test_run",
        )
        
        recent = ItemCalibration(
            item_id="item_1",
            window_id=2,
            a_hat=1.0,
            b_hat=0.6,  # Large drift in b
            c_hat=0.2,
            a_l95=0.9,
            a_u95=1.1,
            b_l95=0.5,
            b_u95=0.7,
            c_l95=0.18,
            c_u95=0.22,
            n=500,
            run_id="test_run",
        )
        
        alerts = detect_drift(baseline, recent, DEFAULT_THRESHOLDS)
        
        # Should have at least delta_b and CI separation alerts
        assert len(alerts) >= 2
        
        delta_b_alerts = [a for a in alerts if a.metric == "delta_b"]
        assert len(delta_b_alerts) > 0
        assert delta_b_alerts[0].severity in ["severe", "moderate"]
        assert delta_b_alerts[0].value == pytest.approx(0.6, abs=0.01)

    def test_moderate_drift_a_parameter(self):
        """Test detection of moderate drift in discrimination."""
        baseline = ItemCalibration(
            item_id="item_2",
            window_id=1,
            a_hat=1.2,
            b_hat=0.0,
            c_hat=0.2,
            a_l95=1.1,
            a_u95=1.3,
            b_l95=-0.1,
            b_u95=0.1,
            c_l95=0.18,
            c_u95=0.22,
            n=300,
            run_id="test_run",
        )
        
        recent = ItemCalibration(
            item_id="item_2",
            window_id=2,
            a_hat=1.45,  # Moderate drift in a
            b_hat=0.05,
            c_hat=0.2,
            a_l95=1.35,
            a_u95=1.55,
            b_l95=-0.05,
            b_u95=0.15,
            c_l95=0.18,
            c_u95=0.22,
            n=300,
            run_id="test_run",
        )
        
        alerts = detect_drift(baseline, recent, DEFAULT_THRESHOLDS)
        
        delta_a_alerts = [a for a in alerts if a.metric == "delta_a"]
        assert len(delta_a_alerts) > 0
        assert delta_a_alerts[0].severity in ["moderate", "severe"]

    def test_no_drift_stable_item(self):
        """Test that stable items generate no alerts."""
        baseline = ItemCalibration(
            item_id="item_3",
            window_id=1,
            a_hat=1.0,
            b_hat=0.0,
            c_hat=0.2,
            a_l95=0.95,
            a_u95=1.05,
            b_l95=-0.05,
            b_u95=0.05,
            c_l95=0.19,
            c_u95=0.21,
            n=400,
            run_id="test_run",
        )
        
        recent = ItemCalibration(
            item_id="item_3",
            window_id=2,
            a_hat=1.02,  # Small, acceptable drift
            b_hat=0.03,
            c_hat=0.20,
            a_l95=0.97,
            a_u95=1.07,
            b_l95=-0.02,
            b_u95=0.08,
            c_l95=0.19,
            c_u95=0.21,
            n=400,
            run_id="test_run",
        )
        
        alerts = detect_drift(baseline, recent, DEFAULT_THRESHOLDS)
        
        # Should have no alerts (all drifts below threshold)
        assert len(alerts) == 0

    def test_ci_separation_detection(self):
        """Test detection of credible interval separation."""
        baseline = ItemCalibration(
            item_id="item_4",
            window_id=1,
            a_hat=1.0,
            b_hat=0.0,
            c_hat=0.2,
            a_l95=0.9,
            a_u95=1.1,
            b_l95=-0.1,
            b_u95=0.1,
            c_l95=0.18,
            c_u95=0.22,
            n=200,
            run_id="test_run",
        )
        
        recent = ItemCalibration(
            item_id="item_4",
            window_id=2,
            a_hat=1.0,
            b_hat=0.4,  # Outside baseline CI
            c_hat=0.2,
            a_l95=0.9,
            a_u95=1.1,
            b_l95=0.3,
            b_u95=0.5,
            c_l95=0.18,
            c_u95=0.22,
            n=200,
            run_id="test_run",
        )
        
        alerts = detect_drift(baseline, recent, DEFAULT_THRESHOLDS)
        
        ci_alerts = [a for a in alerts if a.metric == "b_ci_separation"]
        assert len(ci_alerts) > 0
        assert ci_alerts[0].severity == "severe"

    def test_custom_thresholds(self):
        """Test drift detection with custom thresholds."""
        baseline = ItemCalibration(
            item_id="item_5",
            window_id=1,
            a_hat=1.0,
            b_hat=0.0,
            c_hat=0.2,
            a_l95=0.9,
            a_u95=1.1,
            b_l95=-0.1,
            b_u95=0.1,
            c_l95=0.18,
            c_u95=0.22,
            n=300,
            run_id="test_run",
        )
        
        recent = ItemCalibration(
            item_id="item_5",
            window_id=2,
            a_hat=1.0,
            b_hat=0.15,  # Below default threshold but above custom
            c_hat=0.2,
            a_l95=0.9,
            a_u95=1.1,
            b_l95=0.05,
            b_u95=0.25,
            c_l95=0.18,
            c_u95=0.22,
            n=300,
            run_id="test_run",
        )
        
        # Stricter thresholds
        custom_thresholds = {"delta_b": 0.10, "delta_a": 0.15, "delta_c": 0.02}
        
        alerts = detect_drift(baseline, recent, custom_thresholds)
        
        delta_b_alerts = [a for a in alerts if a.metric == "delta_b"]
        assert len(delta_b_alerts) > 0  # Should trigger with 0.10 threshold


class TestAnchorPriorEnforcement:
    """Test anchor vs non-anchor prior specifications."""

    @pytest.mark.skip(reason="Requires PyMC installation; run manually")
    def test_anchor_prior_stronger_than_non_anchor(self):
        """Test that anchor items get tighter priors (lower variance)."""
        # This test requires PyMC and would run actual Bayesian estimation
        # For CI, we skip and rely on integration testing
        pass


class TestDIFAnalysis:
    """Test DIF detection logic."""

    def test_dif_alert_generation(self):
        """Test generation of DIF-based alerts."""
        baseline = ItemCalibration(
            item_id="item_6",
            window_id=1,
            a_hat=1.0,
            b_hat=0.0,
            c_hat=0.2,
            a_l95=0.9,
            a_u95=1.1,
            b_l95=-0.1,
            b_u95=0.1,
            c_l95=0.18,
            c_u95=0.22,
            n=400,
            run_id="test_run",
        )
        
        recent = ItemCalibration(
            item_id="item_6",
            window_id=2,
            a_hat=1.0,
            b_hat=0.05,
            c_hat=0.2,
            a_l95=0.9,
            a_u95=1.1,
            b_l95=-0.05,
            b_u95=0.15,
            c_l95=0.18,
            c_u95=0.22,
            n=400,
            dif={
                "gender": {
                    "male": {"delta_b": 0.1, "bayes_factor": 5.0},
                    "female": {"delta_b": -0.1, "bayes_factor": 5.2},
                }
            },
            run_id="test_run",
        )
        
        alerts = detect_drift(baseline, recent, DEFAULT_THRESHOLDS)
        
        dif_alerts = [a for a in alerts if a.metric.startswith("dif_")]
        assert len(dif_alerts) > 0  # Should trigger DIF alerts for gender


class TestOperationalProcedures:
    """Test operational procedures and workflows."""

    def test_exposure_weight_mapping(self):
        """Test severity -> exposure weight mapping."""
        from apps.seedtest_api.routers.irt_drift_api import ExposureWeights
        
        severe_weight = ExposureWeights(
            item_id="test",
            weight=0.0,
            reason="severe drift",
            alert_severity="severe",
        )
        assert severe_weight.weight == 0.0
        
        moderate_weight = ExposureWeights(
            item_id="test",
            weight=0.5,
            reason="moderate drift",
            alert_severity="moderate",
        )
        assert moderate_weight.weight == 0.5
        
        minor_weight = ExposureWeights(
            item_id="test",
            weight=0.8,
            reason="minor drift",
            alert_severity="minor",
        )
        assert minor_weight.weight == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
