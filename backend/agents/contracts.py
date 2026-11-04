"""PROJECT LASTLINE: Typed Message Contracts for Specialized Agents.

Defines Pydantic v2 data models for inter-agent communication,
ensuring strict schemas, deterministic behavior, and advisory-only guarantees.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    SENTINEL = "SENTINEL"
    INTEGRITY = "INTEGRITY"
    RECONSTRUCTION = "RECONSTRUCTION"
    IMPACT = "IMPACT"
    RESPONSE = "RESPONSE"
    EXPLAINER = "EXPLAINER"


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TrustStatus(str, Enum):
    TRUSTED = "TRUSTED"
    DEGRADED = "DEGRADED"
    COMPROMISED = "COMPROMISED"


# 1. Sentinel Agent Contracts
class CyberAlert(BaseModel):
    alert_id: str
    plc_id: str
    severity: SeverityLevel
    indicator: str
    details: str
    timestamp: float = 0.0


class SentinelReport(BaseModel):
    cyber_threat_level: SeverityLevel
    flagged_plcs: list[str] = Field(default_factory=list)
    alerts: list[CyberAlert] = Field(default_factory=list)
    timestamp: float = 0.0


# 2. Integrity Agent Contracts
class IntegrityReport(BaseModel):
    system_alarm: bool
    compromised_sensors: list[str] = Field(default_factory=list)
    sensor_trust: dict[str, float] = Field(default_factory=dict)
    plc_trust: dict[str, float] = Field(default_factory=dict)
    timestamp: float = 0.0


# 3. Reconstruction Agent Contracts
class ReconstructionReport(BaseModel):
    stability_index: float = Field(ge=0.0, le=1.0)
    top_suspicious_components: list[dict[str, Any]] = Field(default_factory=list)
    state_estimates: dict[str, float] = Field(default_factory=dict)
    uncertainties: dict[str, float] = Field(default_factory=dict)
    timestamp: float = 0.0


# 4. Impact Agent Contracts
class CriticalFacilityRisk(BaseModel):
    facility_name: str
    zone: str
    min_required_pressure_m: float = 20.0
    current_estimated_pressure_m: float = 20.0
    risk_level: SeverityLevel = SeverityLevel.LOW


class ImpactReport(BaseModel):
    overall_severity: SeverityLevel
    zone_priorities: list[str] = Field(default_factory=list)
    critical_facilities_at_risk: list[dict[str, Any]] = Field(default_factory=list)
    pressure_deficits_m: dict[str, float] = Field(default_factory=dict)
    tanks_time_to_empty_hours: dict[str, float] = Field(default_factory=dict)
    timestamp: float = 0.0


# 5. Response Agent Contracts
class PlaybookAction(BaseModel):
    action_id: str
    title: str
    target_component: str
    recommended_state: str
    requires_human_approval: bool = True
    is_advisory: bool = True
    simulated_in_twin: bool = True
    expected_pressure_gain_m: float = 0.0
    risk_tradeoffs: list[str] = Field(default_factory=list)


class ResponseReport(BaseModel):
    selected_playbook_id: str
    recommended_actions: list[PlaybookAction] = Field(default_factory=list)
    timestamp: float = 0.0


# 6. Explainer Agent Contracts
class EvidencePair(BaseModel):
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    key_assumptions: list[str] = Field(default_factory=list)


class ExplainerReport(BaseModel):
    summary: str
    evidence: EvidencePair
    confidence: float = Field(ge=0.0, le=1.0)
    sandbox_advisory_notice: str = (
        "SANDBOX ENVIRONMENT – ADVISORY ONLY – AUTOMATED PHYSICAL COMMAND EXECUTION FORBIDDEN"
    )
    timestamp: float = 0.0


# End-to-End Orchestration Container
class PipelineResult(BaseModel):
    sentinel: SentinelReport
    integrity: IntegrityReport
    reconstruction: ReconstructionReport
    impact: ImpactReport
    response: ResponseReport
    explainer: ExplainerReport
    audit_entries_count: int
