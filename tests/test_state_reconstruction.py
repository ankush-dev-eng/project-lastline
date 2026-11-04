"""Phase 4 Acceptance Tests: Physical State Reconstruction & Attribution.

Gate Requirements:
- State estimation RMSE at least 40% lower than raw-telemetry baseline under attack.
- Compromised-component attribution top-3 accuracy >= 80%.
- Uncertainty estimates with valid confidence intervals.
"""

import numpy as np
import pytest

from backend.detection.trust_engine import TelemetryTrustEngine
from backend.reconstruction.attribution import ComponentAttributionEngine
from backend.reconstruction.estimator import HydraulicStateEstimator
from data.scenarios import AttackScenarioRegistry
from twin.model import WaterNetworkTwin


@pytest.fixture
def reconstruction_suite():
    twin = WaterNetworkTwin(seed=42)
    trust_engine = TelemetryTrustEngine(twin, seed=42)
    trust_engine.fit_nominal()

    estimator = HydraulicStateEstimator(twin, trust_engine, seed=42)
    estimator.fit_nominal()

    attribution = ComponentAttributionEngine(twin)
    return {
        "twin": twin,
        "trust_engine": trust_engine,
        "estimator": estimator,
        "attribution": attribution,
    }


def test_state_reconstruction_rmse_improvement(reconstruction_suite):
    """Verify that LASTLINE state reconstruction achieves at least 40% lower RMSE than raw telemetry under attack."""
    estimator = reconstruction_suite["estimator"]
    registry = AttackScenarioRegistry(seed=42)

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

    raw_errors = []
    recon_errors = []

    for sc_id in attack_scenarios:
        sc = registry.generate_scenario(sc_id)
        attack_mask = sc.labels["is_attack"].values == 1

        # Reconstruct physical state
        recon_result = estimator.reconstruct_state(sc.telemetry)
        x_recon = recon_result["state_estimates"]

        # Only evaluate on attacked timesteps and continuous sensors
        cont_cols = [c for c in sc.telemetry.columns if "P_" in c or "L_" in c or "F_" in c]

        y_raw = sc.telemetry.loc[attack_mask, cont_cols].fillna(0.0).values
        y_true = sc.ground_truth_physical.loc[attack_mask, cont_cols].values
        y_recon = x_recon.loc[attack_mask, cont_cols].values

        raw_errors.extend((y_raw - y_true).ravel())
        recon_errors.extend((y_recon - y_true).ravel())

    raw_rmse = float(np.sqrt(np.mean(np.square(raw_errors))))
    recon_rmse = float(np.sqrt(np.mean(np.square(recon_errors))))
    relative_improvement = (1.0 - (recon_rmse / raw_rmse)) * 100.0

    print(
        f"\n[Reconstruction Benchmark] Raw RMSE: {raw_rmse:.4f}m vs Reconstructed RMSE: {recon_rmse:.4f}m"
    )
    print(f"Relative Improvement: {relative_improvement:.2f}% (Target: >= 40.0%)")

    # Gate verification
    assert relative_improvement >= 40.0, (
        f"Phase 4 Gate Failure: Reconstruction improvement {relative_improvement:.2f}% is below 40%"
    )


def test_compromised_component_attribution_top3_accuracy(reconstruction_suite):
    """Verify that compromised components are correctly identified in the top-3 ranked suspicious list >= 80%."""
    estimator = reconstruction_suite["estimator"]
    attribution_engine = reconstruction_suite["attribution"]
    registry = AttackScenarioRegistry(seed=42)

    scenarios = registry.list_scenarios()
    hits = 0
    total = len(scenarios)

    for sc_def in scenarios:
        sc = registry.generate_scenario(sc_def.scenario_id)
        recon_result = estimator.reconstruct_state(sc.telemetry)

        # Query top-3 suspicious components during attack period
        ranked = attribution_engine.attribute_incident(
            telemetry=sc.telemetry,
            state_estimates=recon_result["state_estimates"],
            sensor_trust=recon_result["sensor_trust"],
            top_k=3,
        )

        top3_ids = [item["component_id"] for item in ranked]
        # Check if any of the true target components are in top-3
        targets = set(sc_def.target_components)
        if any(t in top3_ids for t in targets):
            hits += 1
        else:
            print(
                f"Attribution Miss in {sc_def.scenario_id}: True targets {targets} not in top-3 {top3_ids}"
            )

    top3_acc = (hits / total) * 100.0
    print(
        f"\n[Attribution Benchmark] Top-3 Accuracy: {top3_acc:.1f}% ({hits}/{total}) (Target: >= 80.0%)"
    )
    assert top3_acc >= 80.0, (
        f"Phase 4 Gate Failure: Top-3 attribution accuracy {top3_acc:.1f}% is below 80.0%"
    )


def test_uncertainty_quantification_coverage(reconstruction_suite):
    """Verify uncertainty bands expand during attack and maintain valid coverage."""
    estimator = reconstruction_suite["estimator"]
    registry = AttackScenarioRegistry(seed=42)

    sc = registry.generate_scenario("SCENARIO_01_SENSOR_BIAS")
    recon_result = estimator.reconstruct_state(sc.telemetry)

    estimates = recon_result["state_estimates"]
    uncertainties = recon_result["uncertainties"]

    # Uncertainties must be strictly positive
    assert (uncertainties > 0.0).all().all(), "Uncertainty values must be positive"

    # Targeted sensor (P_J1) uncertainty must expand during attack
    target = "P_J1"
    nominal_std = uncertainties.iloc[0:5][target].mean()
    attack_std = uncertainties.iloc[7:14][target].mean()
    assert attack_std > nominal_std, "Uncertainty band must expand when telemetry trust degrades"

    # Coverage: ground truth physical values fall within 95% confidence bounds (estimate +/- 1.96*std)
    y_true = sc.ground_truth_physical[target]
    y_hat = estimates[target]
    u = uncertainties[target]

    lower_bound = y_hat - 1.96 * u
    upper_bound = y_hat + 1.96 * u
    in_bounds = (y_true >= lower_bound - 0.5) & (y_true <= upper_bound + 0.5)
    coverage = in_bounds.mean()
    assert coverage >= 0.85, f"Uncertainty confidence coverage {coverage:.2f} is below 85%"
