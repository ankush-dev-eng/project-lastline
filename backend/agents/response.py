"""PROJECT LASTLINE: Response & Advisory Playbook Agent.

Matches verified operational anomalies and hydraulic deficits against
pre-approved municipal emergency response playbooks for human operator approval.

HARD SAFETY GUARANTEE:
All proposed actions are strictly ADVISORY and require human operator confirmation.
No automated physical control command execution exists in this platform.
"""

import time

from backend.agents.contracts import (
    ImpactReport,
    PlaybookAction,
    ReconstructionReport,
    ResponseReport,
)


class ResponseAgent:
    """Specialized agent generating safe, pre-simulated emergency fallback procedures."""

    def determine_response(
        self,
        recon_report: ReconstructionReport,
        impact_report: ImpactReport,
    ) -> ResponseReport:
        """Determines best-matching emergency playbook based on attributed faults and impact."""
        suspicious_ids = [c["component_id"] for c in recon_report.top_suspicious_components]
        top_zone = impact_report.zone_priorities[0] if impact_report.zone_priorities else None

        actions: list[PlaybookAction] = []
        playbook_id = "PB_NOMINAL_MONITORING"

        # Rule 1: PRV or Zone B deficit
        if any("PRV" in s or "V1" in s or "J5" in s for s in suspicious_ids) or (
            top_zone == "Zone_B_Central" and impact_report.pressure_deficits_m.get("Zone_B_Central", 0.0) > 0.0
        ):
            playbook_id = "PB_ZONE_B_EMERGENCY_FEED"
            actions.append(
                PlaybookAction(
                    action_id="ACT-B01",
                    title="Manual Valve Override: Open Emergency Intertie P_INTER_BC",
                    target_component="P_INTER_BC",
                    recommended_state="OPEN",
                    requires_human_approval=True,
                    is_advisory=True,
                    simulated_in_twin=True,
                    expected_pressure_gain_m=6.8,
                    risk_tradeoffs=["Slightly reduces pressure head in Zone C by ~1.2m"],
                )
            )
            actions.append(
                PlaybookAction(
                    action_id="ACT-B02",
                    title="Isolate Compromised PRV Controller PLC 3",
                    target_component="PLC_3",
                    recommended_state="MANUAL_LOCAL_CONTROL",
                    requires_human_approval=True,
                    is_advisory=True,
                    simulated_in_twin=True,
                    expected_pressure_gain_m=0.0,
                    risk_tradeoffs=["Requires physical dispatch of field technician to Station B"],
                )
            )

        # Rule 2: Booster Pump P1 or Zone A deficit
        elif any("P1" in s or "P2" in s or "J1" in s or "T1" in s for s in suspicious_ids) or top_zone == "Zone_A_North":
            playbook_id = "PB_ZONE_A_AUX_BOOSTER_SWAP"
            actions.append(
                PlaybookAction(
                    action_id="ACT-A01",
                    title="Engage Auxiliary Booster Pump P2",
                    target_component="P2_AuxBooster",
                    recommended_state="OPEN",
                    requires_human_approval=True,
                    is_advisory=True,
                    simulated_in_twin=True,
                    expected_pressure_gain_m=8.5,
                    risk_tradeoffs=["Increases electrical energy consumption by 45 kW"],
                )
            )
            actions.append(
                PlaybookAction(
                    action_id="ACT-A02",
                    title="Lock Elevated Tank T1 Gravity Reserve",
                    target_component="P_A_TANK",
                    recommended_state="RESTRICTED_DISCHARGE",
                    requires_human_approval=True,
                    is_advisory=True,
                    simulated_in_twin=True,
                    expected_pressure_gain_m=2.0,
                    risk_tradeoffs=["Preserves 8 hours additional reserve for high-elevation hospital zone"],
                )
            )

        # Rule 3: Tank or Zone C industrial exposure
        elif top_zone == "Zone_C_Industrial" or any("T2" in s for s in suspicious_ids):
            playbook_id = "PB_ZONE_C_INDUSTRIAL_STABILIZATION"
            actions.append(
                PlaybookAction(
                    action_id="ACT-C01",
                    title="Throttled Supply Priority to Industrial Feeder P_C_TANK",
                    target_component="P_C_TANK",
                    recommended_state="PARTIAL_OPEN",
                    requires_human_approval=True,
                    is_advisory=True,
                    simulated_in_twin=True,
                    expected_pressure_gain_m=3.5,
                    risk_tradeoffs=["Non-critical commercial users may experience 10% lower peak pressure"],
                )
            )

        else:
            # Fallback conservative advisory
            playbook_id = "PB_SYSTEM_OBSERVABILITY_FALLBACK"
            actions.append(
                PlaybookAction(
                    action_id="ACT-GEN01",
                    title="Transition SCADA to Independent Acoustic & Ultrasonic Sensor Feeds",
                    target_component="SCADA_GATEWAY",
                    recommended_state="INDEPENDENT_OBSERVABILITY",
                    requires_human_approval=True,
                    is_advisory=True,
                    simulated_in_twin=True,
                    expected_pressure_gain_m=0.0,
                    risk_tradeoffs=["Ignores potentially spoofed PLC telemetry until field audit clears PLCs"],
                )
            )

        return ResponseReport(
            selected_playbook_id=playbook_id,
            recommended_actions=actions,
            timestamp=time.time(),
        )
