"""Phase 2 Acceptance Tests: Attack & Failure Scenario Injector & Dataset Ingestion.

Gate Requirements:
- At least 10 labelled seeded scenarios covering:
  sensor spoofing, replay attacks, PLC setpoint tampering, communication loss, sensor dropout, etc.
- Scenarios are reproducible with identical seeds.
- BATADAL ingestion aligns with standard schema and labels.
"""

import numpy as np
import pytest

from data.scenarios import AttackScenarioRegistry, AttackType, ScenarioResult
from data.batadal import load_batadal_benchmark


@pytest.fixture
def registry():
    return AttackScenarioRegistry(seed=42)


def test_scenario_registry_has_at_least_10_scenarios(registry):
    """Verify that at least 10 distinct operational attack/failure scenarios are registered."""
    scenarios = registry.list_scenarios()
    assert len(scenarios) >= 10, f"Expected >= 10 scenarios, found {len(scenarios)}"

    types_covered = {s.attack_type for s in scenarios}
    assert AttackType.SENSOR_BIAS_SPOOFING in types_covered
    assert AttackType.SENSOR_DRIFT_SPOOFING in types_covered
    assert AttackType.SENSOR_FROZEN_STUCK in types_covered
    assert AttackType.REPLAY_ATTACK in types_covered
    assert AttackType.PLC_SETPOINT_TAMPERING in types_covered
    assert AttackType.COMMUNICATION_LOSS in types_covered
    assert AttackType.SENSOR_DROPOUT in types_covered
    assert AttackType.COORDINATED_FDIA in types_covered
    assert AttackType.STEALTH_FALSE_DATA in types_covered
    assert AttackType.VALVE_TAMPERING in types_covered


def test_scenario_execution_and_schema(registry):
    """Verify that executing a scenario returns properly typed and labeled telemetry and ground truth."""
    scenario_id = "SCENARIO_01_SENSOR_BIAS"
    result: ScenarioResult = registry.generate_scenario(scenario_id)

    assert result.scenario_id == scenario_id
    assert len(result.telemetry) > 0
    assert len(result.ground_truth_physical) == len(result.telemetry)
    assert len(result.labels) == len(result.telemetry)

    # Check columns
    assert "is_attack" in result.labels.columns
    assert "attack_type" in result.labels.columns
    assert "target_components" in result.labels.columns

    # Verify that an attack interval actually exists
    attack_steps = result.labels["is_attack"].sum()
    assert attack_steps > 0, "Scenario must contain at least one attacked timestep"

    # Verify reported telemetry diverges from physical ground truth during attack
    target = result.target_components[0]
    attack_mask = result.labels["is_attack"] == 1
    diff = np.abs(
        result.telemetry.loc[attack_mask, target]
        - result.ground_truth_physical.loc[attack_mask, target]
    )
    assert (diff > 0.05).any(), "Compromised telemetry must deviate from true physical state"


def test_scenario_reproducibility(registry):
    """Verify that seeded scenario execution is 100% deterministic."""
    reg1 = AttackScenarioRegistry(seed=1337)
    res1 = reg1.generate_scenario("SCENARIO_02_TANK_LEVEL_DRIFT")

    reg2 = AttackScenarioRegistry(seed=1337)
    res2 = reg2.generate_scenario("SCENARIO_02_TANK_LEVEL_DRIFT")

    np.testing.assert_allclose(
        res1.telemetry.values,
        res2.telemetry.values,
        rtol=1e-5,
        atol=1e-5,
        equal_nan=True,
    )
    assert (res1.labels["is_attack"] == res2.labels["is_attack"]).all()


def test_all_10_scenarios_generate_cleanly(registry):
    """Verify that all registered scenarios run to completion and provide valid labels."""
    scenarios = registry.list_scenarios()
    for sc in scenarios:
        res = registry.generate_scenario(sc.scenario_id)
        assert res.labels["is_attack"].sum() > 0, f"Scenario {sc.scenario_id} missing attacks"
        assert not res.telemetry.empty, f"Scenario {sc.scenario_id} telemetry is empty"
        assert not res.ground_truth_physical.empty, f"Scenario {sc.scenario_id} ground truth is empty"


def test_batadal_loader_schema_and_labels():
    """Verify BATADAL dataset ingestion yields structured telemetry and ground truth attack flags."""
    dataset = load_batadal_benchmark()
    assert dataset.telemetry is not None
    assert not dataset.telemetry.empty
    assert "is_attack" in dataset.labels.columns
    assert dataset.labels["is_attack"].sum() > 0
    assert len(dataset.sensor_columns) >= 10
