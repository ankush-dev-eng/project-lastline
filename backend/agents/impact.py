"""PROJECT LASTLINE: Impact Assessment & Downstream Disruption Agent.

Evaluates pressure deficits, critical customer risk (hospitals, industrial data centres),
and storage tank depletion to prioritise intervention across distribution zones.
"""

import time
from typing import Any

from backend.agents.contracts import ImpactReport, ReconstructionReport, SeverityLevel
from twin.model import WaterNetworkTwin


class ImpactAgent:
    """Specialized agent assessing physical disruption and municipal service exposure."""

    def __init__(self, twin: WaterNetworkTwin):
        self.twin = twin
        self.critical_facilities = [
            {
                "facility_name": "Verdant Memorial Hospital",
                "zone": "Zone_B_Central",
                "node_id": "J6",
                "min_pressure_m": 22.0,
            },
            {
                "facility_name": "Eastside High-Tech Industrial Park",
                "zone": "Zone_C_Industrial",
                "node_id": "J10",
                "min_pressure_m": 20.0,
            },
            {
                "facility_name": "North Highlands Civic Center",
                "zone": "Zone_A_North",
                "node_id": "J2",
                "min_pressure_m": 18.0,
            },
        ]

    def assess(self, recon_report: ReconstructionReport) -> ImpactReport:
        """Assesses downstream disruption and ranks zones by priority."""
        estimates = recon_report.state_estimates

        # Pressure deficit calculations per zone
        zone_pressures: dict[str, list[float]] = {
            "Zone_A_North": [],
            "Zone_B_Central": [],
            "Zone_C_Industrial": [],
        }

        for j_idx in range(1, 5):
            k = f"P_J{j_idx}"
            if k in estimates:
                zone_pressures["Zone_A_North"].append(estimates[k])

        for j_idx in range(5, 9):
            k = f"P_J{j_idx}"
            if k in estimates:
                zone_pressures["Zone_B_Central"].append(estimates[k])

        for j_idx in range(9, 13):
            k = f"P_J{j_idx}"
            if k in estimates:
                zone_pressures["Zone_C_Industrial"].append(estimates[k])

        min_req_pressure = 20.0
        deficits: dict[str, float] = {}
        for zone, pressures in zone_pressures.items():
            if pressures:
                min_p = min(pressures)
                deficits[zone] = round(max(0.0, min_req_pressure - min_p), 2)
            else:
                deficits[zone] = 0.0

        # Critical facilities check
        facilities_at_risk: list[dict[str, Any]] = []
        for fac in self.critical_facilities:
            node_key = f"P_{fac['node_id']}"
            p_val = estimates.get(node_key, 25.0)
            if p_val < fac["min_pressure_m"]:
                facilities_at_risk.append(
                    {
                        "facility_name": fac["facility_name"],
                        "zone": fac["zone"],
                        "min_required_pressure_m": fac["min_pressure_m"],
                        "current_estimated_pressure_m": round(p_val, 2),
                        "deficit_m": round(fac["min_pressure_m"] - p_val, 2),
                        "risk_level": SeverityLevel.CRITICAL if fac["min_pressure_m"] - p_val > 5.0 else SeverityLevel.HIGH,
                    }
                )

        # Tanks time to empty (estimated reserve hours based on current reconstructed level)
        tanks_tte: dict[str, float] = {}
        t1_level = estimates.get("L_T1", 5.0)
        t2_level = estimates.get("L_T2", 4.5)
        # Assuming nominal hourly depletion rate of 0.25 m/hr under outage
        tanks_tte["T1_Highlands"] = round(max(0.5, (t1_level - 1.5) / 0.25), 1)
        tanks_tte["T2_Eastside"] = round(max(0.5, (t2_level - 1.5) / 0.25), 1)

        # Zone prioritisation ranking
        def zone_priority_score(zone: str) -> float:
            score = deficits.get(zone, 0.0) * 2.0
            if any(f["zone"] == zone for f in facilities_at_risk):
                score += 15.0
            return score

        sorted_zones = sorted(
            ["Zone_B_Central", "Zone_A_North", "Zone_C_Industrial"],
            key=zone_priority_score,
            reverse=True,
        )

        # Overall severity determination
        max_deficit = max(deficits.values()) if deficits else 0.0
        if facilities_at_risk or max_deficit > 8.0:
            severity = SeverityLevel.CRITICAL
        elif max_deficit > 3.0:
            severity = SeverityLevel.HIGH
        elif max_deficit > 0.5 or recon_report.stability_index < 0.85:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW

        return ImpactReport(
            overall_severity=severity,
            zone_priorities=sorted_zones,
            critical_facilities_at_risk=facilities_at_risk,
            pressure_deficits_m=deficits,
            tanks_time_to_empty_hours=tanks_tte,
            timestamp=time.time(),
        )
