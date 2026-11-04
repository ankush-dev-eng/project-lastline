"""PROJECT LASTLINE: Automated Benchmark Runner.

Executes real empirical evaluations across all active phase gates and updates BENCHMARKS.md.
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from backend.detection.baselines import FixedThresholdDetector
from backend.detection.trust_engine import TelemetryTrustEngine
from data.scenarios import AttackScenarioRegistry
from twin.model import WaterNetworkTwin

ROOT_DIR = Path(__file__).resolve().parent.parent
BENCHMARKS_FILE = ROOT_DIR / "BENCHMARKS.md"


def get_git_commit() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def evaluate_phase3_benchmarks(seed: int = 42) -> dict[str, float]:
    """Runs empirical evaluation of Phase 3 anomaly detection on held-out test scenarios."""
    twin = WaterNetworkTwin(seed=seed)
    engine = TelemetryTrustEngine(twin, seed=seed)
    engine.fit_nominal()

    baseline = FixedThresholdDetector(twin)
    registry = AttackScenarioRegistry(seed=seed)

    test_ids = [
        "SCENARIO_08_COORDINATED_FDIA",
        "SCENARIO_09_STEALTH_FALSE_DATA",
        "SCENARIO_10_VALVE_TAMPERING",
        "SCENARIO_11_MULTI_PLC_COORDINATED",
    ]

    all_y_true, all_y_pred_engine, all_y_pred_base = [], [], []
    engine_ttds, base_ttds = [], []

    for sc_id in test_ids:
        sc = registry.generate_scenario(sc_id)
        spec = registry.get_scenario(sc_id)
        start_hr = spec.start_hour
        y_true = sc.labels["is_attack"].values

        # LASTLINE Detection
        ev_eng = engine.evaluate_telemetry(sc.telemetry)
        y_pred_eng = ev_eng["system_alarm"].values
        eng_alarms = np.where(y_pred_eng)[0]
        valid_eng = [s for s in eng_alarms if s >= start_hr]
        engine_ttds.append((valid_eng[0] - start_hr) if valid_eng else 24)

        # Baseline Detection
        ev_base = baseline.evaluate_telemetry(sc.telemetry)
        y_pred_base = ev_base["system_alarm"].values
        base_alarms = np.where(y_pred_base)[0]
        valid_base = [s for s in base_alarms if s >= start_hr]
        base_ttds.append((valid_base[0] - start_hr) if valid_base else 24)

        all_y_true.extend(y_true)
        all_y_pred_engine.extend(y_pred_eng)
        all_y_pred_base.extend(y_pred_base)

    y_true_arr = np.array(all_y_true)
    y_eng_arr = np.array(all_y_pred_engine)
    y_base_arr = np.array(all_y_pred_base)

    # LASTLINE Metrics
    tp = np.sum((y_true_arr == 1) & (y_eng_arr == 1))
    fp = np.sum((y_true_arr == 0) & (y_eng_arr == 1))
    tn = np.sum((y_true_arr == 0) & (y_eng_arr == 0))
    fn = np.sum((y_true_arr == 1) & (y_eng_arr == 0))

    prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    mean_ttd = float(np.mean(engine_ttds))

    # Baseline Metrics
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
    }


def run_benchmark():
    commit = get_git_commit()
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"Running PROJECT LASTLINE Benchmark Suite [Commit: {commit}, Time: {timestamp}]")

    metrics = evaluate_phase3_benchmarks()
    print("\n=== Phase 3: Telemetry Anomaly Detection & Trust Scoring ===")
    print(
        f"LASTLINE Engine: F1={metrics['engine_f1']:.4f}, Prec={metrics['engine_prec']:.4f}, "
        f"Rec={metrics['engine_rec']:.4f}, FPR={metrics['engine_fpr'] * 100:.2f}%, TTD={metrics['engine_ttd']:.2f}h"
    )
    print(
        f"Naive Baseline:   F1={metrics['baseline_f1']:.4f}, Prec={metrics['baseline_prec']:.4f}, "
        f"Rec={metrics['baseline_rec']:.4f}, FPR={metrics['baseline_fpr'] * 100:.2f}%, TTD={metrics['baseline_ttd']:.2f}h"
    )

    # Gate check
    assert metrics["engine_f1"] >= 0.85, f"Phase 3 Gate F1 unmet: {metrics['engine_f1']}"
    assert metrics["engine_fpr"] <= 0.05, f"Phase 3 Gate FPR unmet: {metrics['engine_fpr']}"
    assert metrics["engine_ttd"] < metrics["baseline_ttd"], "Phase 3 Gate TTD unmet"
    print(">> Phase 3 Gate: PASSED (F1 >= 0.85, FPR <= 5%, TTD better than baseline)\n")


if __name__ == "__main__":
    run_benchmark()
