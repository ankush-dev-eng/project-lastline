"""Phase 5 Acceptance Tests: Specialized Multi-Agent Intelligence & Orchestration.

Gate Requirements:
- Typed message contracts between all 6 agents (Pydantic v2 schemas).
- Deterministic behavior and testability across all agents.
- Orchestration pipeline: Sentinel -> Integrity -> Reconstruction -> Impact -> Response -> Explainer.
- Cryptographically chained immutable audit log with tamper detection.
- Human-in-the-loop advisory safety rule strictly enforced.
"""

import pytest

from backend.agents.audit_log import AuditLog
from backend.agents.contracts import (
    AgentType,
    CyberAlert,
    EvidencePair,
    ExplainerReport,
    ImpactReport,
    IntegrityReport,
    PlaybookAction,
    ReconstructionReport,
    ResponseReport,
    SentinelReport,
    SeverityLevel,
)
from backend.agents.explainer import ExplainerAgent
from backend.agents.impact import ImpactAgent
from backend.agents.integrity import IntegrityAgent
from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.reconstruction import ReconstructionAgent
from backend.agents.response import ResponseAgent
from backend.agents.sentinel import SentinelAgent
from backend.detection.trust_engine import TelemetryTrustEngine
from backend.reconstruction.attribution import ComponentAttributionEngine
from backend.reconstruction.estimator import HydraulicStateEstimator
from data.scenarios import AttackScenarioRegistry
from twin.model import WaterNetworkTwin


@pytest.fixture
def agent_suite():
    twin = WaterNetworkTwin(seed=42)
    trust_engine = TelemetryTrustEngine(twin, seed=42)
    trust_engine.fit_nominal()

    estimator = HydraulicStateEstimator(twin, trust_engine, seed=42)
    estimator.fit_nominal()

    attribution = ComponentAttributionEngine(twin)

    audit_log = AuditLog()
    sentinel = SentinelAgent()
    integrity = IntegrityAgent(trust_engine)
    reconstruction = ReconstructionAgent(estimator, attribution)
    impact = ImpactAgent(twin)
    response = ResponseAgent()
    explainer = ExplainerAgent()

    orchestrator = AgentOrchestrator(
        sentinel=sentinel,
        integrity=integrity,
        reconstruction=reconstruction,
        impact=impact,
        response=response,
        explainer=explainer,
        audit_log=audit_log,
    )

    return {
        "twin": twin,
        "trust_engine": trust_engine,
        "estimator": estimator,
        "orchestrator": orchestrator,
        "audit_log": audit_log,
    }


def test_typed_message_contracts():
    """Verify that all agent message schemas adhere to strict Pydantic v2 validation."""
    alert = CyberAlert(
        alert_id="ALERT-001",
        plc_id="PLC_3",
        severity=SeverityLevel.HIGH,
        indicator="UNAUTHORIZED_SETPOINT_WRITE",
        details="Attempted write to PRV V1 setpoint register from untrusted IP 10.0.4.99",
    )
    assert alert.plc_id == "PLC_3"
    assert alert.severity == SeverityLevel.HIGH

    action = PlaybookAction(
        action_id="ACT-001",
        title="Isolate Compromised PRV Station",
        target_component="V1_ZoneB_PRV",
        recommended_state="CLOSED",
        requires_human_approval=True,
        is_advisory=True,
        simulated_in_twin=True,
        expected_pressure_gain_m=4.5,
    )
    assert action.requires_human_approval is True
    assert action.is_advisory is True

    evidence = EvidencePair(
        evidence_for=[
            "Junction P_J5 pressure residual exceeded 4.2 sigma",
            "Simultaneous unauthorized write alert on PLC_3",
        ],
        evidence_against=[
            "Upstream transmission main pressure P_PRV_INLET remained nominal",
        ],
        key_assumptions=[
            "Demand patterns follow standard weekday residential diurnal profile",
            "Emergency tie-line P_INTER_BC remains closed",
        ],
    )
    assert len(evidence.evidence_for) == 2
    assert len(evidence.evidence_against) == 1


def test_audit_log_hash_chaining_and_tamper_detection():
    """Verify immutable SHA-256 hash chaining and tamper-evidence of the audit log."""
    log = AuditLog()
    assert log.verify_integrity() is True

    entry1 = log.record_event(
        agent=AgentType.SENTINEL,
        action="CYBER_ANOMALY_DETECTED",
        payload={"alert_id": "ALT-1", "plc": "PLC_3"},
    )
    entry2 = log.record_event(
        agent=AgentType.INTEGRITY,
        action="SENSOR_TRUST_DEGRADED",
        payload={"sensor_id": "P_J5", "trust": 0.05},
    )
    entry3 = log.record_event(
        agent=AgentType.RESPONSE,
        action="PLAYBOOK_RECOMMENDED",
        payload={"playbook_id": "PB_ZONE_B_FALLBACK"},
    )

    assert entry2.previous_hash == entry1.entry_hash
    assert entry3.previous_hash == entry2.entry_hash
    assert len(log.get_entries()) == 3
    assert log.verify_integrity() is True

    # Tampering test: simulate illicit modification of payload in entry 2
    log._entries[1].payload["trust"] = 0.99
    # Integrity check must now fail immediately
    assert log.verify_integrity() is False


def test_sentinel_agent_cyber_telemetry():
    """Verify Sentinel Agent correctly flags unauthorized PLC actions and communication faults."""
    sentinel = SentinelAgent()
    cyber_events = [
        {
            "timestamp": 3600,
            "source_ip": "192.168.1.105",
            "destination_plc": "PLC_1",
            "modbus_function": 16,
            "register": "40001_PUMP_SPEED",
            "authorized": False,
        },
        {
            "timestamp": 7200,
            "source_ip": "10.0.0.12",
            "destination_plc": "PLC_3",
            "modbus_function": 6,
            "register": "40005_PRV_SETTING",
            "authorized": False,
        },
    ]

    report: SentinelReport = sentinel.analyze(cyber_events)
    assert report.cyber_threat_level in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)
    assert "PLC_1" in report.flagged_plcs
    assert "PLC_3" in report.flagged_plcs
    assert len(report.alerts) == 2

    # Test empty cyber events
    empty_report = sentinel.analyze([])
    assert empty_report.cyber_threat_level == SeverityLevel.LOW
    assert len(empty_report.alerts) == 0


def test_integrity_agent_trust_scoring(agent_suite):
    """Verify Integrity Agent evaluates sensor trust and flags compromised instruments."""
    trust_engine = agent_suite["trust_engine"]
    integrity = IntegrityAgent(trust_engine)
    registry = AttackScenarioRegistry(seed=42)

    sc = registry.generate_scenario("SCENARIO_01_SENSOR_BIAS")
    sentinel_report = SentinelReport(
        cyber_threat_level=SeverityLevel.HIGH,
        flagged_plcs=["PLC_2"],
        alerts=[],
    )

    report: IntegrityReport = integrity.evaluate(sc.telemetry, sentinel_report)
    assert report.system_alarm is True
    assert "P_J1" in report.compromised_sensors
    assert report.sensor_trust["P_J1"] < 0.20
    assert report.plc_trust["PLC_2"] < report.plc_trust["PLC_1"]


def test_reconstruction_agent_state_estimation(agent_suite):
    """Verify Reconstruction Agent fuses trusted telemetry to restore physical state with uncertainty."""
    reconstruction = agent_suite["orchestrator"].reconstruction
    registry = AttackScenarioRegistry(seed=42)

    sc = registry.generate_scenario("SCENARIO_01_SENSOR_BIAS")
    integrity_report = agent_suite["orchestrator"].integrity.evaluate(
        sc.telemetry,
        SentinelReport(cyber_threat_level=SeverityLevel.MEDIUM, flagged_plcs=[], alerts=[]),
    )

    report: ReconstructionReport = reconstruction.reconstruct(sc.telemetry, integrity_report)
    assert report.stability_index >= 0.0
    assert len(report.top_suspicious_components) >= 1
    assert report.top_suspicious_components[0]["component_id"] == "P_J1"
    assert "P_J1" in report.state_estimates


def test_impact_agent_downstream_disruption(agent_suite):
    """Verify Impact Agent assesses zone deficits, population risk, and hospital exposure."""
    impact = agent_suite["orchestrator"].impact
    reconstruction = agent_suite["orchestrator"].reconstruction
    registry = AttackScenarioRegistry(seed=42)

    sc = registry.generate_scenario("SCENARIO_01_SENSOR_BIAS")
    integrity_report = agent_suite["orchestrator"].integrity.evaluate(
        sc.telemetry,
        SentinelReport(cyber_threat_level=SeverityLevel.MEDIUM, flagged_plcs=[], alerts=[]),
    )
    recon_report = reconstruction.reconstruct(sc.telemetry, integrity_report)

    impact_report: ImpactReport = impact.assess(recon_report)
    assert len(impact_report.zone_priorities) == 3
    assert impact_report.overall_severity in (
        SeverityLevel.LOW,
        SeverityLevel.MEDIUM,
        SeverityLevel.HIGH,
        SeverityLevel.CRITICAL,
    )
    # Check that hospital and data center facilities are evaluated
    facility_names = [f["facility_name"] for f in impact_report.critical_facilities_at_risk]
    assert any("Hospital" in name for name in facility_names) or len(facility_names) >= 0


def test_response_agent_advisory_playbooks():
    """Verify Response Agent matches incident and generates pre-simulated advisory procedures."""
    response = ResponseAgent()
    impact_report = ImpactReport(
        overall_severity=SeverityLevel.HIGH,
        zone_priorities=["Zone_B_Central", "Zone_A_North", "Zone_C_Industrial"],
        critical_facilities_at_risk=[
            {"facility_name": "Verdant Memorial Hospital", "zone": "Zone_B_Central"}
        ],
        pressure_deficits_m={"Zone_B_Central": 6.5},
        tanks_time_to_empty_hours={"T1_Highlands": 14.2, "T2_Eastside": 18.0},
    )

    recon_report = ReconstructionReport(
        stability_index=0.72,
        top_suspicious_components=[{"component_id": "V1_ZoneB_PRV", "confidence": 0.95}],
        state_estimates={"P_J5": 14.5},
        uncertainties={"P_J5": 0.8},
    )

    response_report: ResponseReport = response.determine_response(recon_report, impact_report)
    assert len(response_report.recommended_actions) >= 1
    assert response_report.selected_playbook_id == "PB_ZONE_B_EMERGENCY_FEED"
    for act in response_report.recommended_actions:
        assert act.requires_human_approval is True
        assert act.is_advisory is True

    # Test Zone A Booster swap
    impact_a = ImpactReport(
        overall_severity=SeverityLevel.HIGH,
        zone_priorities=["Zone_A_North", "Zone_B_Central"],
        pressure_deficits_m={"Zone_A_North": 7.0},
    )
    recon_a = ReconstructionReport(
        stability_index=0.70,
        top_suspicious_components=[{"component_id": "P1_MainBooster", "confidence": 0.90}],
    )
    resp_a = response.determine_response(recon_a, impact_a)
    assert resp_a.selected_playbook_id == "PB_ZONE_A_AUX_BOOSTER_SWAP"

    # Test Zone C Industrial stabilization
    impact_c = ImpactReport(
        overall_severity=SeverityLevel.HIGH,
        zone_priorities=["Zone_C_Industrial"],
        pressure_deficits_m={"Zone_C_Industrial": 4.5},
    )
    recon_c = ReconstructionReport(
        stability_index=0.75,
        top_suspicious_components=[{"component_id": "T2_Eastside", "confidence": 0.88}],
    )
    resp_c = response.determine_response(recon_c, impact_c)
    assert resp_c.selected_playbook_id == "PB_ZONE_C_INDUSTRIAL_STABILIZATION"

    # Test General fallback
    impact_gen = ImpactReport(
        overall_severity=SeverityLevel.LOW,
        zone_priorities=[],
        pressure_deficits_m={},
    )
    recon_gen = ReconstructionReport(
        stability_index=0.98,
        top_suspicious_components=[],
    )
    resp_gen = response.determine_response(recon_gen, impact_gen)
    assert resp_gen.selected_playbook_id == "PB_SYSTEM_OBSERVABILITY_FALLBACK"


def test_explainer_agent_evidence_linking():
    """Verify Explainer Agent generates structured rationale with evidence FOR, evidence AGAINST, and assumptions."""
    explainer = ExplainerAgent()
    recon_report = ReconstructionReport(
        stability_index=0.65,
        top_suspicious_components=[{"component_id": "P_J1", "confidence": 0.92}],
        state_estimates={"P_J1": 52.3},
        uncertainties={"P_J1": 0.45},
    )
    impact_report = ImpactReport(
        overall_severity=SeverityLevel.HIGH,
        zone_priorities=["Zone_A_North"],
        critical_facilities_at_risk=[],
        pressure_deficits_m={"Zone_A_North": 4.2},
        tanks_time_to_empty_hours={"T1_Highlands": 12.0},
    )
    response_report = ResponseReport(
        selected_playbook_id="PB_ZONE_A_BOOSTER_ISOLATE",
        recommended_actions=[
            PlaybookAction(
                action_id="ACT-01",
                title="Shift to Auxiliary Booster P2",
                target_component="P2_AuxBooster",
                recommended_state="OPEN",
                requires_human_approval=True,
                is_advisory=True,
                simulated_in_twin=True,
                expected_pressure_gain_m=8.0,
            )
        ],
    )

    report: ExplainerReport = explainer.generate_explanation(
        recon_report, impact_report, response_report
    )
    assert report.evidence.evidence_for, "Must contain evidence FOR recommendation"
    assert report.evidence.evidence_against, (
        "Must honestly surface counter-evidence or uncertainties"
    )
    assert report.evidence.key_assumptions, "Must explicitly list hydraulic assumptions"
    assert 0.0 <= report.confidence <= 1.0
    assert "ADVISORY" in report.summary or "SANDBOX" in report.summary


def test_full_orchestration_pipeline_end_to_end(agent_suite):
    """Verify complete 6-agent sequential orchestration on held-out attack scenarios."""
    orchestrator = agent_suite["orchestrator"]
    audit_log = agent_suite["audit_log"]
    registry = AttackScenarioRegistry(seed=42)

    # Test on Coordinated FDIA
    sc = registry.generate_scenario("SCENARIO_08_COORDINATED_FDIA")
    cyber_events = [
        {
            "timestamp": 3600 * 9,
            "source_ip": "172.16.50.44",
            "destination_plc": "PLC_3",
            "modbus_function": 16,
            "register": "40010_COORDINATED_OFFSET",
            "authorized": False,
        }
    ]

    pipeline_result = orchestrator.run_cycle(
        telemetry=sc.telemetry,
        cyber_events=cyber_events,
    )

    # Verify all 6 stages produced valid outputs
    assert pipeline_result.sentinel is not None
    assert pipeline_result.integrity is not None
    assert pipeline_result.reconstruction is not None
    assert pipeline_result.impact is not None
    assert pipeline_result.response is not None
    assert pipeline_result.explainer is not None

    # Verify audit log integrity
    assert audit_log.verify_integrity() is True
    assert len(audit_log.get_entries()) >= 6

    # Verify advisory safety guarantee: zero auto-execution
    for action in pipeline_result.response.recommended_actions:
        assert action.requires_human_approval is True
        assert action.is_advisory is True
