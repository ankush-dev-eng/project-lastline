"""PROJECT LASTLINE: Multi-Agent Pipeline Orchestrator.

Sequentially coordinates Sentinel, Integrity, Reconstruction, Impact, Response, and Explainer agents,
recording all message exchanges and state transitions in the cryptographic audit log.
"""

from typing import Any

import pandas as pd

from backend.agents.audit_log import AuditLog
from backend.agents.contracts import (
    AgentType,
    ExplainerReport,
    ImpactReport,
    IntegrityReport,
    PipelineResult,
    ReconstructionReport,
    ResponseReport,
    SentinelReport,
)
from backend.agents.explainer import ExplainerAgent
from backend.agents.impact import ImpactAgent
from backend.agents.integrity import IntegrityAgent
from backend.agents.reconstruction import ReconstructionAgent
from backend.agents.response import ResponseAgent
from backend.agents.sentinel import SentinelAgent


class AgentOrchestrator:
    """Central orchestrator driving the 6-agent cyber-resilience assessment loop."""

    def __init__(
        self,
        sentinel: SentinelAgent,
        integrity: IntegrityAgent,
        reconstruction: ReconstructionAgent,
        impact: ImpactAgent,
        response: ResponseAgent,
        explainer: ExplainerAgent,
        audit_log: AuditLog | None = None,
    ):
        self.sentinel = sentinel
        self.integrity = integrity
        self.reconstruction = reconstruction
        self.impact = impact
        self.response = response
        self.explainer = explainer
        self.audit_log = audit_log or AuditLog()

    def run_cycle(
        self,
        telemetry: pd.DataFrame,
        cyber_events: list[dict[str, Any]] | None = None,
        timestep_idx: int | None = None,
    ) -> PipelineResult:
        """Executes a complete single-step multi-agent assessment cycle."""
        # 1. Sentinel Agent: Cyber Telemetry & Protocol Inspection
        sentinel_rep: SentinelReport = self.sentinel.analyze(cyber_events)
        self.audit_log.record_event(
            agent=AgentType.SENTINEL,
            action="CYBER_TELEMETRY_ANALYZED",
            payload={
                "cyber_threat_level": sentinel_rep.cyber_threat_level.value,
                "flagged_plcs": sentinel_rep.flagged_plcs,
                "alerts_count": len(sentinel_rep.alerts),
            },
        )

        # 2. Integrity Agent: Physical Sensor Trust Scoring
        integrity_rep: IntegrityReport = self.integrity.evaluate(
            telemetry, sentinel_rep, timestep_idx=timestep_idx
        )
        self.audit_log.record_event(
            agent=AgentType.INTEGRITY,
            action="TELEMETRY_TRUST_SCORED",
            payload={
                "system_alarm": integrity_rep.system_alarm,
                "compromised_sensors": integrity_rep.compromised_sensors,
                "mean_sensor_trust": round(
                    sum(integrity_rep.sensor_trust.values()) / max(len(integrity_rep.sensor_trust), 1),
                    3,
                ),
            },
        )

        # 3. Reconstruction Agent: Physics-Constrained State Estimation
        recon_rep: ReconstructionReport = self.reconstruction.reconstruct(
            telemetry, integrity_rep, timestep_idx=timestep_idx
        )
        self.audit_log.record_event(
            agent=AgentType.RECONSTRUCTION,
            action="PHYSICAL_STATE_RECONSTRUCTED",
            payload={
                "stability_index": round(recon_rep.stability_index, 3),
                "top_suspicious": [c["component_id"] for c in recon_rep.top_suspicious_components[:3]],
            },
        )

        # 4. Impact Agent: Downstream Disruption & Zone Prioritisation
        impact_rep: ImpactReport = self.impact.assess(recon_rep)
        self.audit_log.record_event(
            agent=AgentType.IMPACT,
            action="DISRUPTION_IMPACT_ASSESSED",
            payload={
                "overall_severity": impact_rep.overall_severity.value,
                "zone_priorities": impact_rep.zone_priorities,
                "critical_facilities_count": len(impact_rep.critical_facilities_at_risk),
            },
        )

        # 5. Response Agent: Pre-Simulated Advisory Fallback Selection
        response_rep: ResponseReport = self.response.determine_response(recon_rep, impact_rep)
        self.audit_log.record_event(
            agent=AgentType.RESPONSE,
            action="FALLBACK_PLAYBOOK_PROPOSED",
            payload={
                "selected_playbook_id": response_rep.selected_playbook_id,
                "actions_count": len(response_rep.recommended_actions),
                "all_advisory": all(a.is_advisory for a in response_rep.recommended_actions),
                "requires_approval": all(a.requires_human_approval for a in response_rep.recommended_actions),
            },
        )

        # 6. Explainer Agent: Evidence-Linked Rationale Synthesis
        explainer_rep: ExplainerReport = self.explainer.generate_explanation(
            recon_rep,
            impact_rep,
            response_rep,
        )
        self.audit_log.record_event(
            agent=AgentType.EXPLAINER,
            action="EXPLANATION_SYNTHESIZED",
            payload={
                "confidence": explainer_rep.confidence,
                "evidence_for_count": len(explainer_rep.evidence.evidence_for),
                "evidence_against_count": len(explainer_rep.evidence.evidence_against),
            },
        )

        return PipelineResult(
            sentinel=sentinel_rep,
            integrity=integrity_rep,
            reconstruction=recon_rep,
            impact=impact_rep,
            response=response_rep,
            explainer=explainer_rep,
            audit_entries_count=len(self.audit_log.get_entries()),
        )
