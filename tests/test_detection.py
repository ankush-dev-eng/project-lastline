"""Phase 3 Acceptance Tests: Anomaly Detection & Telemetry Trust Scoring.

Gate Requirements:
- Held-out test scenarios: F1 >= 0.85 and FPR <= 5.0%
- Time-to-Detect (TTD) reported and strictly better than the fixed-threshold baseline
- Continuous trust scores T_i(t) in [0.0, 1.0] computed per sensor and per PLC
"""

import numpy as np
import pytest

from backend.detection.baselines import FixedThresholdDetector
from backend.detection.trust_engine import TelemetryTrustEngine
from data.scenarios import AttackScenarioRegistry
from twin.model import WaterNetworkTwin


@pytest.fixture
def detector_fixture():
    twin = WaterNetworkTwin(seed=42)
    engine = TelemetryTrustEngine(twin=twin, seed=42)
    # Fit on nominal baseline operation (no attack data leaked into training)
    engine.fit_nominal()
    return engine


@pytest.fixture
def baseline_fixture():
    twin = WaterNetworkTwin(seed=42)
    return FixedThresholdDetector(twin=twin)


def test_held_out_test_set_performance(detector_fixture):
    """Verify that LASTLINE achieves F1 >= 0.85 and FPR <= 5.0% on strictly held-out test scenarios."""
    registry = AttackScenarioRegistry(seed=42)
    # Strictly held-out test scenarios: Scenarios 8, 9, 10, 11
    test_scenario_ids = [
        "SCENARIO_08_COORDINATED_FDIA",
        "SCENARIO_09_STEALTH_FALSE_DATA",
        "SCENARIO_10_VALVE_TAMPERING",
        "SCENARIO_11_MULTI_PLC_COORDINATED",
    ]

    all_y_true = []
    all_y_pred = []

    for sc_id in test_scenario_ids:
        scenario = registry.generate_scenario(sc_id)
        y_true = scenario.labels["is_attack"].values

        # Run detection
        trust_results = detector_fixture.evaluate_telemetry(scenario.telemetry)
        y_pred = trust_results["system_alarm"].values

        all_y_true.extend(y_true)
        all_y_pred.extend(y_pred)

    y_true_arr = np.array(all_y_true)
    y_pred_arr = np.array(all_y_pred)

    # Compute Confusion Matrix Metrics
    tp = np.sum((y_true_arr == 1) & (y_pred_arr == 1))
    fp = np.sum((y_true_arr == 0) & (y_pred_arr == 1))
    tn = np.sum((y_true_arr == 0) & (y_pred_arr == 0))
    fn = np.sum((y_true_arr == 1) & (y_pred_arr == 0))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print(
        f"\n[Held-Out Test Results] Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}, FPR: {fpr:.4f}"
    )

    # Enforce Phase 3 Gate Criteria
    assert f1 >= 0.85, f"Phase 3 Gate Failure: F1 score {f1:.4f} is below target 0.85"
    assert fpr <= 0.05, (
        f"Phase 3 Gate Failure: False Positive Rate {fpr:.4f} exceeds target 0.05 (5%)"
    )


def test_time_to_detect_better_than_baseline(detector_fixture, baseline_fixture):
    """Verify that LASTLINE time-to-detect (TTD) strictly outperforms the static-threshold baseline."""
    registry = AttackScenarioRegistry(seed=42)
    scenarios_to_evaluate = [
        "SCENARIO_01_SENSOR_BIAS",
        "SCENARIO_02_TANK_LEVEL_DRIFT",
        "SCENARIO_08_COORDINATED_FDIA",
        "SCENARIO_09_STEALTH_FALSE_DATA",
    ]

    engine_ttds = []
    baseline_ttds = []

    for sc_id in scenarios_to_evaluate:
        scenario = registry.generate_scenario(sc_id)
        spec = registry.get_scenario(sc_id)
        attack_start_hr = spec.start_hour

        # LASTLINE Detection
        engine_eval = detector_fixture.evaluate_telemetry(scenario.telemetry)
        engine_alarms = np.where(engine_eval["system_alarm"].values)[0]
        # Alarms at or after attack start
        valid_engine_alarms = [step for step in engine_alarms if step >= attack_start_hr]
        engine_ttd = (valid_engine_alarms[0] - attack_start_hr) if valid_engine_alarms else 24

        # Baseline Detection
        base_eval = baseline_fixture.evaluate_telemetry(scenario.telemetry)
        base_alarms = np.where(base_eval["system_alarm"].values)[0]
        valid_base_alarms = [step for step in base_alarms if step >= attack_start_hr]
        baseline_ttd = (valid_base_alarms[0] - attack_start_hr) if valid_base_alarms else 24

        engine_ttds.append(engine_ttd)
        baseline_ttds.append(baseline_ttd)

    mean_engine_ttd = np.mean(engine_ttds)
    mean_baseline_ttd = np.mean(baseline_ttds)

    print(
        f"\n[TTD Benchmark] LASTLINE Mean TTD: {mean_engine_ttd:.2f}h vs Baseline: {mean_baseline_ttd:.2f}h"
    )
    assert mean_engine_ttd < mean_baseline_ttd, (
        f"LASTLINE TTD ({mean_engine_ttd:.2f}h) must be strictly better than baseline ({mean_baseline_ttd:.2f}h)"
    )


def test_sensor_and_plc_trust_scoring(detector_fixture):
    """Verify continuous trust scoring per sensor channel and per PLC."""
    registry = AttackScenarioRegistry(seed=42)
    # Scenario 1 targets P_J1 on PLC 2 starting at hour 6
    scenario = registry.generate_scenario("SCENARIO_01_SENSOR_BIAS")

    eval_result = detector_fixture.evaluate_telemetry(scenario.telemetry)
    sensor_trust = eval_result["sensor_trust"]
    plc_trust = eval_result["plc_trust"]

    # Before attack (hour 0-5), trust must be high across all sensors
    nominal_trust = sensor_trust.iloc[0:5]["P_J1"].mean()
    assert nominal_trust >= 0.85, f"Nominal trust score {nominal_trust} too low"

    # During attack (hour 7-14), attacked sensor trust must drop dramatically
    attack_trust = sensor_trust.iloc[7:14]["P_J1"].mean()
    assert attack_trust <= 0.30, f"Attacked sensor trust {attack_trust} did not drop below 0.30"

    # PLC 2 trust must drop relative to other uncompromised PLCs (e.g. PLC 1)
    plc2_attack_trust = plc_trust.iloc[7:14]["PLC_2"].mean()
    plc1_attack_trust = plc_trust.iloc[7:14]["PLC_1"].mean()
    assert plc2_attack_trust < plc1_attack_trust, (
        "Targeted PLC trust must be lower than unaffected PLC"
    )
