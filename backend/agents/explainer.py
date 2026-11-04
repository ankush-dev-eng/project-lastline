"""PROJECT LASTLINE: Explainer Agent (Evidence-Linked Rationale).

Synthesizes physical telemetry evidence, cyber alerts, and digital twin simulation results
into an explainable report for human control-room operators.
Explicitly contrasts Evidence FOR, Evidence AGAINST, key assumptions, and confidence bands.
"""

import time

from backend.agents.contracts import (
    EvidencePair,
    ExplainerReport,
    ImpactReport,
    ReconstructionReport,
    ResponseReport,
)


class ExplainerAgent:
    """Specialized agent synthesizing explainable rationale and evidence balance sheets."""

    def generate_explanation(
        self,
        recon_report: ReconstructionReport,
        impact_report: ImpactReport,
        response_report: ResponseReport,
    ) -> ExplainerReport:
        """Constructs an evidence-backed rationale for the current operational recommendation."""
        top_suspicious = recon_report.top_suspicious_components
        primary_fault = top_suspicious[0]["component_id"] if top_suspicious else "None"
        fault_conf = top_suspicious[0].get("confidence", 0.85) if top_suspicious else 0.50

        top_zone = impact_report.zone_priorities[0] if impact_report.zone_priorities else "General Network"
        deficit = impact_report.pressure_deficits_m.get(top_zone, 0.0)
        action_count = len(response_report.recommended_actions)

        # 1. Evidence FOR the diagnosis and recommendation
        evidence_for: list[str] = [
            f"Component '{primary_fault}' identified as primary anomaly source with {fault_conf*100:.1f}% confidence.",
            f"Physical state reconstruction indicates a {deficit:.1f}m pressure deficit in {top_zone}.",
        ]
        if impact_report.critical_facilities_at_risk:
            fac_names = ", ".join(f["facility_name"] for f in impact_report.critical_facilities_at_risk)
            evidence_for.append(f"Immediate risk identified for critical facilities: {fac_names}.")

        # 2. Evidence AGAINST / Key Uncertainties (honest counter-evidence)
        evidence_against: list[str] = [
            f"Network state reconstructed under partial observability with system stability index at {recon_report.stability_index*100:.1f}%.",
            "Uncertainty bands in adjacent unmonitored branch pipes remain unconstrained by direct telemetry.",
        ]
        if any(c.get("confidence", 0.0) < 0.70 for c in top_suspicious[:2]):
            evidence_against.append("Secondary suspicious component attribution carries moderate ambiguity (<70% confidence).")

        # 3. Key Assumptions
        key_assumptions: list[str] = [
            "Customer consumer demands conform to standard diurnal municipal demand patterns.",
            "Underground pipe structural roughness coefficients (C-factors) remain at calibrated baseline values.",
            "Digital twin EPANET hydraulic model accurately captures boundary head at the North Water Treatment Plant.",
        ]

        # 4. Synthesize human-readable summary
        summary = (
            f"SANDBOX ADVISORY SUMMARY: Critical resilience advisory for {top_zone}. "
            f"Physical state reconstruction attributes primary telemetry corruption to '{primary_fault}'. "
            f"Simulated emergency fallback playbook '{response_report.selected_playbook_id}' proposes "
            f"{action_count} advisory intervention(s) to restore hydraulic head and protect municipal service continuity. "
            f"All physical control actions remain in sandbox mode and strictly require human operator confirmation."
        )

        confidence = round(float(recon_report.stability_index * 0.4 + fault_conf * 0.6), 2)
        confidence = float(max(0.10, min(0.99, confidence)))

        return ExplainerReport(
            summary=summary,
            evidence=EvidencePair(
                evidence_for=evidence_for,
                evidence_against=evidence_against,
                key_assumptions=key_assumptions,
            ),
            confidence=confidence,
            timestamp=time.time(),
        )
