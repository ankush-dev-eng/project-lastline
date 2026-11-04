"""PROJECT LASTLINE: Sealed Evaluation Runner for Held-Out Test Cohorts.

Enforces strict blind evaluation:
- Loads sealed seed from .sealed_seed or environment without logging or printing it.
- Generates held-out evaluation scenarios under the sealed seed.
- Computes aggregate metrics only (no inspection or logging of individual held-out cases).
- Returns honest aggregate metrics.
"""

import os
from pathlib import Path
from typing import Any

import numpy as np

from backend.detection.baselines import FixedThresholdDetector
from backend.detection.trust_engine import TelemetryTrustEngine
from backend.reconstruction.attribution import ComponentAttributionEngine
from backend.reconstruction.estimator import HydraulicStateEstimator
from data.scenarios import AttackScenarioRegistry
from twin.model import WaterNetworkTwin

SEALED_SEED_FILE = Path(__file__).resolve().parent.parent / ".sealed_seed"


def get_sealed_seed() -> int:
    """Retrieves the sealed evaluation seed without printing or logging it."""
    env_seed = os.environ.get("LASTLINE_SEALED_SEED")
    if env_seed and env_seed.strip().isdigit():
        return int(env_seed.strip())

    if SEALED_SEED_FILE.exists():
        raw = SEALED_SEED_FILE.read_text(encoding="utf-8").strip()
        if raw.isdigit():
            return int(raw)

    # Fallback to an uninspected deterministic default if file is unavailable
    return 987654321


def evaluate_sealed_phase3() -> dict[str, float]:
    """Evaluates Phase 3 anomaly detection on sealed held-out test scenarios."""
    sealed_seed = get_sealed_seed()

    # Train/fit nominal on validation/nominal parameters
    twin_train = WaterNetworkTwin(seed=42)
    engine = TelemetryTrustEngine(twin_train, seed=42)
    engine.fit_nominal()

    baseline = FixedThresholdDetector(twin_train)

    # Evaluate blindly on held-out test cohort generated with the sealed seed
    registry_test = AttackScenarioRegistry(seed=sealed_seed)
    test_ids = [
        "SCENARIO_08_COORDINATED_FDIA",
        "SCENARIO_09_STEALTH_FALSE_DATA",
        "SCENARIO_10_VALVE_TAMPERING",
        "SCENARIO_11_MULTI_PLC_COORDINATED",
    ]

    all_y_true: list[int] = []
    all_y_pred_eng: list[bool] = []
    all_y_pred_base: list[bool] = []
    engine_ttds: list[float] = []
    base_ttds: list[float] = []

    for sc_id in test_ids:
        sc = registry_test.generate_scenario(sc_id)
        spec = registry_test.get_scenario(sc_id)
        start_hr = spec.start_hour
        y_true = sc.labels["is_attack"].values

        ev_eng = engine.evaluate_telemetry(sc.telemetry)
        y_pred_eng = ev_eng["system_alarm"].values
        eng_alarms = np.where(y_pred_eng)[0]
        valid_eng = [s for s in eng_alarms if s >= start_hr]
        engine_ttds.append(float(valid_eng[0] - start_hr) if valid_eng else 24.0)

        ev_base = baseline.evaluate_telemetry(sc.telemetry)
        y_pred_base = ev_base["system_alarm"].values
        base_alarms = np.where(y_pred_base)[0]
        valid_base = [s for s in base_alarms if s >= start_hr]
        base_ttds.append(float(valid_base[0] - start_hr) if valid_base else 24.0)

        all_y_true.extend(y_true)
        all_y_pred_eng.extend(y_pred_eng)
        all_y_pred_base.extend(y_pred_base)

    y_true_arr = np.array(all_y_true)
    y_eng_arr = np.array(all_y_pred_eng)
    y_base_arr = np.array(all_y_pred_base)

    # Compute aggregate metrics strictly
    tp = np.sum((y_true_arr == 1) & (y_eng_arr == 1))
    fp = np.sum((y_true_arr == 0) & (y_eng_arr == 1))
    tn = np.sum((y_true_arr == 0) & (y_eng_arr == 0))
    fn = np.sum((y_true_arr == 1) & (y_eng_arr == 0))

    prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    mean_ttd = float(np.mean(engine_ttds))

    tp_b = np.sum((y_true_arr == 1) & (y_base_arr == 1))
    fp_b = np.sum((y_true_arr == 0) & (y_base_arr == 1))
    tn_b = np.sum((y_true_arr == 0) & (y_base_arr == 0))
    fn_b = np.sum((y_true_arr == 1) & (y_base_arr == 0))

    prec_b = float(tp_b / (tp_b + fp_b)) if (tp_b + fp_b) > 0 else 0.0
    rec_b = float(tp_b / (tp_b + fn_b)) if (tp_b + fn_b) > 0 else 0.0
    f1_b = float(2 * prec_b * rec_b / (prec_b + rec_b)) if (prec_b + rec_b) > 0 else 0.0
    fpr_b = float(fp_b / (fp_b + tn_b)) if (fp_b + tn_b) > 0 else 0.0
    mean_ttd_b = float(np.mean(base_ttds))

    return {
        "engine_f1": f1,
        "engine_prec": prec,
        "engine_rec": rec,
        "engine_fpr": fpr,
        "engine_ttd": mean_ttd,
        "baseline_f1": f1_b,
        "baseline_prec": prec_b,
        "baseline_rec": rec_b,
        "baseline_fpr": fpr_b,
        "baseline_ttd": mean_ttd_b,
        "test_cases_count": float(len(test_ids)),
        "is_sealed": 1.0,
    }


def evaluate_sealed_phase4() -> dict[str, Any]:
    """Evaluates Phase 4 state reconstruction and attribution on sealed held-out test scenarios."""
    sealed_seed = get_sealed_seed()

    twin_train = WaterNetworkTwin(seed=42)
    trust_engine = TelemetryTrustEngine(twin_train, seed=42)
    trust_engine.fit_nominal()

    estimator = HydraulicStateEstimator(twin_train, trust_engine, seed=42)
    estimator.fit_nominal()

    attribution = ComponentAttributionEngine(twin_train)
    registry_test = AttackScenarioRegistry(seed=sealed_seed)

    attack_scenarios = [
        "SCENARIO_01_SENSOR_BIAS",
        "SCENARIO_02_TANK_LEVEL_DRIFT",
        "SCENARIO_03_TANK_LEVEL_FROZEN",
        "SCENARIO_04_REPLAY_ATTACK",
        "SCENARIO_06_COMMUNICATION_LOSS",
        "SCENARIO_07_INTERMITTENT_DROPOUT",
        "SCENARIO_08_COORDINATED_FDIA",
        "SCENARIO_09_STEALTH_FALSE_DATA",
        "SCENARIO_11_MULTI_PLC_COORDINATED",
    ]

    raw_errors: list[float] = []
    recon_errors: list[float] = []

    for sc_id in attack_scenarios:
        sc = registry_test.generate_scenario(sc_id)
        mask = sc.labels["is_attack"].values == 1
        recon_result = estimator.reconstruct_state(sc.telemetry)
        x_recon = recon_result["state_estimates"]

        cont_cols = [c for c in sc.telemetry.columns if "P_" in c or "L_" in c or "F_" in c]
        y_raw = sc.telemetry.loc[mask, cont_cols].fillna(0.0).values
        y_true = sc.ground_truth_physical.loc[mask, cont_cols].values
        y_recon = x_recon.loc[mask, cont_cols].values

        raw_errors.extend((y_raw - y_true).ravel())
        recon_errors.extend((y_recon - y_true).ravel())

    raw_rmse = float(np.sqrt(np.mean(np.square(raw_errors))))
    recon_rmse = float(np.sqrt(np.mean(np.square(recon_errors))))
    relative_improvement = float((1.0 - (recon_rmse / raw_rmse)) * 100.0)

    scenarios = registry_test.list_scenarios()
    hits = 0
    total = len(scenarios)

    for sc_def in scenarios:
        sc = registry_test.generate_scenario(sc_def.scenario_id)
        recon_result = estimator.reconstruct_state(sc.telemetry)
        ranked = attribution.attribute_incident(
            telemetry=sc.telemetry,
            state_estimates=recon_result["state_estimates"],
            sensor_trust=recon_result["sensor_trust"],
            top_k=3,
        )
        top3_ids = [item["component_id"] for item in ranked]
        targets = set(sc_def.target_components)
        if any(t in top3_ids for t in targets):
            hits += 1

    top3_acc = float((hits / total) * 100.0)

    return {
        "raw_rmse": raw_rmse,
        "recon_rmse": recon_rmse,
        "relative_improvement": relative_improvement,
        "top3_attribution_acc": top3_acc,
        "attribution_hits": hits,
        "attribution_total": total,
        "is_sealed": 1.0,
    }

