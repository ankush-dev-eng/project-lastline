"""Phase 6 Acceptance Tests: Recommendations & Digital Twin Pre-Simulation.

Gate Requirements:
- 100% of shown recommendations satisfy minimum-pressure (P >= 15.0m) and tank-level constraints.
- Any candidate playbook that violates physical constraints is rejected in simulation and never shown.
- Every shown recommendation carries evidence FOR, evidence AGAINST, confidence score, and assumptions list.
- All recommendations require human-in-the-loop approval and are strictly advisory.
"""

import pytest

from backend.agents.contracts import SeverityLevel
from backend.playbooks.catalog import FallbackPlaybookCatalog
from backend.playbooks.engine import RecommendationEngine
from backend.playbooks.simulator import TwinPlaybookSimulator
from data.scenarios import AttackScenarioRegistry
from twin.model import WaterNetworkTwin


@pytest.fixture
def playbook_suite():
    twin = WaterNetworkTwin(seed=42)
    simulator = TwinPlaybookSimulator(twin)
    catalog = FallbackPlaybookCatalog()
    engine = RecommendationEngine(twin=twin, simulator=simulator, catalog=catalog)
    return {
        "twin": twin,
        "simulator": simulator,
        "catalog": catalog,
        "engine": engine,
    }


def test_twin_simulation_validates_safe_playbooks(playbook_suite):
    """Verify that valid emergency playbooks simulate in WNTR without violating physical constraints."""
    simulator = playbook_suite["simulator"]
    catalog = playbook_suite["catalog"]

    safe_playbooks = [
        "PB_ZONE_B_EMERGENCY_FEED",
        "PB_ZONE_A_AUX_BOOSTER_SWAP",
        "PB_ZONE_C_INDUSTRIAL_STABILIZATION",
        "PB_TANK_STORAGE_PRESERVATION",
    ]

    for pb_id in safe_playbooks:
        playbook = catalog.get_playbook(pb_id)
        result = simulator.simulate_playbook(playbook, duration_hours=24)

        assert result.is_valid is True, (
            f"Playbook {pb_id} failed simulation: {result.constraint_violations}"
        )
        assert result.min_pressure_observed_m >= 15.0, (
            f"Playbook {pb_id} violated minimum pressure: {result.min_pressure_observed_m:.2f}m < 15.0m"
        )
        for tank_id, lvl in result.min_tank_levels.items():
            assert lvl >= 1.5, (
                f"Tank {tank_id} depleted below minimum level in {pb_id}: {lvl:.2f}m < 1.5m"
            )
        for tank_id, lvl in result.max_tank_levels.items():
            assert lvl <= 9.0, (
                f"Tank {tank_id} overflowed maximum level in {pb_id}: {lvl:.2f}m > 9.0m"
            )


def test_twin_simulation_rejects_unsafe_playbooks(playbook_suite):
    """Verify that unsafe playbooks that violate hydraulic limits are strictly caught and rejected."""
    simulator = playbook_suite["simulator"]
    catalog = playbook_suite["catalog"]

    unsafe_playbooks = [
        "PB_UNSAFE_SHUTDOWN_ALL_PUMPS",
        "PB_UNSAFE_DRAIN_TANKS_RAPIDLY",
    ]

    for pb_id in unsafe_playbooks:
        playbook = catalog.get_playbook(pb_id)
        result = simulator.simulate_playbook(playbook, duration_hours=24)

        # Simulation must detect violation and flag invalid
        assert result.is_valid is False, f"Unsafe playbook {pb_id} was erroneously marked valid!"
        assert len(result.constraint_violations) > 0


def test_100_percent_shown_recommendations_satisfy_constraints(playbook_suite):
    """Gate verification: 100% of shown recommendations satisfy minimum pressure and tank constraints."""
    engine = playbook_suite["engine"]
    registry = AttackScenarioRegistry(seed=42)

    scenarios = [
        "SCENARIO_01_SENSOR_BIAS",
        "SCENARIO_02_TANK_LEVEL_DRIFT",
        "SCENARIO_08_COORDINATED_FDIA",
        "SCENARIO_10_VALVE_TAMPERING",
        "SCENARIO_11_MULTI_PLC_COORDINATED",
    ]

    recommendations_shown = 0

    for sc_id in scenarios:
        sc = registry.generate_scenario(sc_id)
        recs = engine.generate_recommendations(
            telemetry=sc.telemetry,
            affected_zone="Zone_B_Central" if "10" in sc_id or "08" in sc_id else "Zone_A_North",
            severity=SeverityLevel.HIGH,
        )

        for rec in recs:
            recommendations_shown += 1
            # Verify twin pre-simulation validation
            assert rec.simulated_safe is True, "Shown recommendation must be verified safe in twin"
            assert rec.simulation_proof["min_pressure_m"] >= 15.0, (
                f"Recommendation {rec.recommendation_id} min pressure {rec.simulation_proof['min_pressure_m']} < 15.0m"
            )
            assert rec.simulation_proof["min_tank_level_m"] >= 1.5, (
                f"Recommendation {rec.recommendation_id} tank level {rec.simulation_proof['min_tank_level_m']} < 1.5m"
            )

    assert recommendations_shown >= 5, (
        "Expected at least 5 validated recommendations across attack scenarios"
    )


def test_recommendation_evidence_confidence_and_assumptions(playbook_suite):
    """Verify that every generated recommendation carries structured evidence, confidence, and assumptions."""
    engine = playbook_suite["engine"]
    registry = AttackScenarioRegistry(seed=42)

    sc = registry.generate_scenario("SCENARIO_10_VALVE_TAMPERING")
    recs = engine.generate_recommendations(
        telemetry=sc.telemetry,
        affected_zone="Zone_B_Central",
        severity=SeverityLevel.CRITICAL,
    )

    assert len(recs) >= 1
    for rec in recs:
        # Structured Evidence
        assert rec.evidence.evidence_for, "Recommendation must carry evidence FOR"
        assert rec.evidence.evidence_against, (
            "Recommendation must honestly surface counter-evidence or risks"
        )
        assert rec.evidence.key_assumptions, (
            "Recommendation must list explicit hydraulic assumptions"
        )
        # Confidence Band
        assert 0.0 <= rec.confidence <= 1.0, f"Confidence {rec.confidence} out of range [0, 1]"
        # Human approval advisory workflow
        assert rec.requires_human_approval is True
        assert rec.is_advisory is True
        assert rec.approval_status == "PENDING_APPROVAL"
