"""PROJECT LASTLINE: Pre-Approved Fallback Playbook Catalog.

Defines site-specific emergency fallback procedures for the Verdant City Water System.
Includes both verified operational fallback playbooks and synthetic unsafe test playbooks
to prove that the digital twin simulator strictly gates and rejects violating procedures.
"""

from typing import Any

from pydantic import BaseModel, Field


class PlaybookIntervention(BaseModel):
    element_id: str
    element_type: str  # "pump", "valve", "pipe", "junction"
    parameter: str  # "status", "setting", "base_demand"
    target_value: Any


class FallbackPlaybook(BaseModel):
    playbook_id: str
    name: str
    description: str
    target_zone: str
    trigger_condition: str
    interventions: list[PlaybookIntervention] = Field(default_factory=list)
    expected_impact: str = ""
    tradeoffs: list[str] = Field(default_factory=list)
    is_safe_baseline: bool = True


class FallbackPlaybookCatalog:
    """Catalog of municipal operational resilience playbooks."""

    def __init__(self):
        self._playbooks: dict[str, FallbackPlaybook] = self._register_playbooks()

    def _register_playbooks(self) -> dict[str, FallbackPlaybook]:
        pbs = [
            FallbackPlaybook(
                playbook_id="PB_ZONE_B_EMERGENCY_FEED",
                name="Zone B Emergency Intertie Feed & PRV Bypass",
                description=(
                    "Opens inter-zone emergency tie line P_INTER_BC to supply Zone B directly from "
                    "Zone C grid while PRV station V1 undergoes local technician inspection."
                ),
                target_zone="Zone_B_Central",
                trigger_condition="PRV station anomaly, pressure deficit in Zone B, or PLC 3 compromise.",
                interventions=[
                    PlaybookIntervention(
                        element_id="P_INTER_BC",
                        element_type="pipe",
                        parameter="status",
                        target_value="OPEN",
                    ),
                ],
                expected_impact="Restores downstream pressure to 28-32m across Zone B commercial grid.",
                tradeoffs=["Draws ~0.04 m3/s additional head from Zone C; monitored to prevent deficit."],
                is_safe_baseline=True,
            ),
            FallbackPlaybook(
                playbook_id="PB_ZONE_A_AUX_BOOSTER_SWAP",
                name="Zone A Auxiliary Booster P2 Activation",
                description=(
                    "Starts standby auxiliary booster pump P2_AuxBooster to maintain transmission "
                    "main flow to elevated residential Zone A in case of P1 trip or speed tampering."
                ),
                target_zone="Zone_A_North",
                trigger_condition="Pump P1 failure, PLC 1 setpoint tampering, or Zone A pressure deficit.",
                interventions=[
                    PlaybookIntervention(
                        element_id="P2_AuxBooster",
                        element_type="pump",
                        parameter="status",
                        target_value="OPEN",
                    ),
                ],
                expected_impact="Supplies steady 75m discharge head to Zone A residential grid.",
                tradeoffs=["Auxiliary pump operates at standard speed; electrical demand increases by 45 kW."],
                is_safe_baseline=True,
            ),
            FallbackPlaybook(
                playbook_id="PB_ZONE_C_INDUSTRIAL_STABILIZATION",
                name="Zone C Industrial Feeder Flow Balancing",
                description=(
                    "Balances discharge to Tank T2 Eastside and throttles non-critical distribution "
                    "to preserve fire protection and hospital reserve volumes."
                ),
                target_zone="Zone_C_Industrial",
                trigger_condition="Eastside Tank T2 draining anomaly or industrial pressure deficit.",
                interventions=[
                    PlaybookIntervention(
                        element_id="P_C_TANK",
                        element_type="pipe",
                        parameter="status",
                        target_value="OPEN",
                    ),
                ],
                expected_impact="Maintains Eastside tank level above 3.5m and protects industrial park feed.",
                tradeoffs=["Slightly reduces peak filling rate during early morning hours."],
                is_safe_baseline=True,
            ),
            FallbackPlaybook(
                playbook_id="PB_TANK_STORAGE_PRESERVATION",
                name="Municipal Storage Tank Emergency Reserve Lock",
                description=(
                    "Enforces dual-pump balanced dispatch to stabilize tank levels across both "
                    "elevated reservoirs T1 and T2 during suspected telemetry blackout."
                ),
                target_zone="Zone_A_North",
                trigger_condition="Simultaneous telemetry dropout on PLC 2 and PLC 4.",
                interventions=[
                    PlaybookIntervention(
                        element_id="P1_MainBooster",
                        element_type="pump",
                        parameter="status",
                        target_value="OPEN",
                    ),
                    PlaybookIntervention(
                        element_id="P_INTER_BC",
                        element_type="pipe",
                        parameter="status",
                        target_value="OPEN",
                    ),
                ],
                expected_impact="Maintains continuous positive head and prevents storage depletion.",
                tradeoffs=["Pre-emptively locks storage reserve until field verification is completed."],
                is_safe_baseline=True,
            ),
            # Intentional UNSAFE test playbooks (must be rejected by simulator)
            FallbackPlaybook(
                playbook_id="PB_UNSAFE_SHUTDOWN_ALL_PUMPS",
                name="Catastrophic Complete Pump Shutdown (Unsafe Test Playbook)",
                description="Closes all pumps simultaneously without auxiliary supply (forbidden).",
                target_zone="Global",
                trigger_condition="Negative control test.",
                interventions=[
                    PlaybookIntervention(
                        element_id="P1_MainBooster",
                        element_type="pump",
                        parameter="status",
                        target_value="CLOSED",
                    ),
                    PlaybookIntervention(
                        element_id="P2_AuxBooster",
                        element_type="pump",
                        parameter="status",
                        target_value="CLOSED",
                    ),
                ],
                expected_impact="Causes severe low-pressure collapse (<15m) across all zones.",
                tradeoffs=["Catastrophic service loss; unacceptable."],
                is_safe_baseline=False,
            ),
            FallbackPlaybook(
                playbook_id="PB_UNSAFE_DRAIN_TANKS_RAPIDLY",
                name="Rapid Tank Depletion (Unsafe Test Playbook)",
                description="Closes supply to elevated tanks causing dryout.",
                target_zone="Zone_A_North",
                trigger_condition="Negative control test.",
                interventions=[
                    PlaybookIntervention(
                        element_id="P_A_TANK",
                        element_type="pipe",
                        parameter="status",
                        target_value="CLOSED",
                    ),
                    PlaybookIntervention(
                        element_id="P1_MainBooster",
                        element_type="pump",
                        parameter="status",
                        target_value="CLOSED",
                    ),
                ],
                expected_impact="Depletes Zone A storage below minimum 1.5m limit.",
                tradeoffs=["Violates storage safety reserve."],
                is_safe_baseline=False,
            ),
        ]
        return {pb.playbook_id: pb for pb in pbs}

    def list_playbooks(self) -> list[FallbackPlaybook]:
        return list(self._playbooks.values())

    def get_playbook(self, playbook_id: str) -> FallbackPlaybook:
        if playbook_id not in self._playbooks:
            raise KeyError(f"Playbook '{playbook_id}' not found in catalog.")
        return self._playbooks[playbook_id]
