"""PROJECT LASTLINE: Shared Application State & Engine Singleton.

Initializes and manages the lifetime of digital twin, multi-agent orchestrator,
reconstruction estimators, and cryptographic audit log.
"""

from typing import Any

from backend.agents.audit_log import AuditLog
from backend.agents.explainer import ExplainerAgent
from backend.agents.impact import ImpactAgent
from backend.agents.integrity import IntegrityAgent
from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.reconstruction import ReconstructionAgent
from backend.agents.response import ResponseAgent
from backend.agents.sentinel import SentinelAgent
from backend.api.replay import ReplayController
from backend.detection.trust_engine import TelemetryTrustEngine
from backend.playbooks.catalog import FallbackPlaybookCatalog
from backend.playbooks.engine import RecommendationEngine, VerifiedRecommendation
from backend.playbooks.simulator import TwinPlaybookSimulator
from backend.reconstruction.attribution import ComponentAttributionEngine
from backend.reconstruction.estimator import HydraulicStateEstimator
from data.scenarios import AttackScenarioRegistry, ScenarioResult
from twin.model import WaterNetworkTwin


class SystemState:
    """Singleton holding the initialized LASTLINE engine components."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.twin = WaterNetworkTwin(seed=seed)
        self.registry = AttackScenarioRegistry(seed=seed)

        self.trust_engine = TelemetryTrustEngine(self.twin, seed=seed)
        self.trust_engine.fit_nominal()

        self.estimator = HydraulicStateEstimator(self.twin, self.trust_engine, seed=seed)
        self.estimator.fit_nominal()

        self.attribution = ComponentAttributionEngine(self.twin)
        self.simulator = TwinPlaybookSimulator(self.twin)
        self.catalog = FallbackPlaybookCatalog()
        self.rec_engine = RecommendationEngine(self.twin, self.simulator, self.catalog)

        self.audit_log = AuditLog()
        self.sentinel = SentinelAgent()
        self.integrity = IntegrityAgent(self.trust_engine)
        self.reconstruction = ReconstructionAgent(self.estimator, self.attribution)
        self.impact = ImpactAgent(self.twin)
        self.response = ResponseAgent()
        self.explainer = ExplainerAgent()

        self.orchestrator = AgentOrchestrator(
            sentinel=self.sentinel,
            integrity=self.integrity,
            reconstruction=self.reconstruction,
            impact=self.impact,
            response=self.response,
            explainer=self.explainer,
            audit_log=self.audit_log,
        )

        self.replay = ReplayController(scenario_id="SCENARIO_01_SENSOR_BIAS")
        self.active_scenario: ScenarioResult = self.registry.generate_scenario("SCENARIO_01_SENSOR_BIAS")
        self.cached_recs: list[VerifiedRecommendation] = []
        self.approval_records: dict[str, dict[str, Any]] = {}

    def load_scenario(self, scenario_id: str) -> None:
        self.active_scenario = self.registry.generate_scenario(scenario_id)
        self.replay.set_scenario(scenario_id)
        self.cached_recs = []

    def get_current_frame(self) -> dict[str, Any]:
        """Calculates current timestep frame based on replay hour."""
        hour = self.replay.current_hour
        telemetry_df = self.active_scenario.telemetry
        hour_clamped = min(hour, len(telemetry_df) - 1)

        # Slice telemetry up to current hour
        sub_telemetry = telemetry_df.iloc[: hour_clamped + 1]

        # Execute single assessment cycle
        res = self.orchestrator.run_cycle(telemetry=sub_telemetry, timestep_idx=hour_clamped)

        # Fetch/update recommendations if alarm active
        if not self.cached_recs:
            top_zone = res.impact.zone_priorities[0] if res.impact.zone_priorities else "Zone_B_Central"
            self.cached_recs = self.rec_engine.generate_recommendations(
                telemetry=sub_telemetry,
                affected_zone=top_zone,
                severity=res.impact.overall_severity,
            )

        # Raw telemetry row
        raw_row = {col: float(telemetry_df[col].iloc[hour_clamped]) for col in telemetry_df.columns}

        return {
            "timestamp": float(telemetry_df.index[hour_clamped]),
            "current_hour": hour_clamped,
            "max_hours": self.replay.max_hours,
            "scenario_id": self.replay.scenario_id,
            "is_playing": self.replay.is_playing,
            "speed": self.replay.speed,
            "telemetry": raw_row,
            "reconstructed_state": res.reconstruction.state_estimates,
            "uncertainties": res.reconstruction.uncertainties,
            "sensor_trust": res.integrity.sensor_trust,
            "plc_trust": res.integrity.plc_trust,
            "system_alarm": res.integrity.system_alarm,
            "stability_index": res.reconstruction.stability_index,
            "top_suspicious": res.reconstruction.top_suspicious_components,
            "zone_priorities": res.impact.zone_priorities,
            "critical_facilities_at_risk": res.impact.critical_facilities_at_risk,
            "pressure_deficits_m": res.impact.pressure_deficits_m,
            "tanks_time_to_empty_hours": res.impact.tanks_time_to_empty_hours,
            "recommendations": [r.model_dump() for r in self.cached_recs],
            "explainer_summary": res.explainer.summary,
            "evidence": res.explainer.evidence.model_dump(),
            "confidence": res.explainer.confidence,
            "agent_reports": {
                "sentinel": res.sentinel.model_dump(),
                "integrity": res.integrity.model_dump(),
                "reconstruction": res.reconstruction.model_dump(),
                "impact": res.impact.model_dump(),
                "response": res.response.model_dump(),
                "explainer": res.explainer.model_dump(),
            },
        }


_GLOBAL_STATE: SystemState | None = None


def get_system_state() -> SystemState:
    global _GLOBAL_STATE
    if _GLOBAL_STATE is None:
        _GLOBAL_STATE = SystemState(seed=42)
    return _GLOBAL_STATE
