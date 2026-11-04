"""PROJECT LASTLINE: Root-Cause Component Attribution Engine.

Identifies and ranks compromised sensors, PLCs, pumps, and valves
based on telemetry trust collapse, reconstruction deviation, and physical topology.
"""

from typing import Any

import numpy as np
import pandas as pd

from twin.model import WaterNetworkTwin


class ComponentAttributionEngine:
    """Attributes cyber incidents to the most probable compromised components."""

    def __init__(self, twin: WaterNetworkTwin):
        self.twin = twin
        self.sensors = twin.get_sensor_registry()

        # Mapping between sensor IDs and parent physical elements
        self.element_mapping: dict[str, str] = {
            "S_P1": "P1_MainBooster",
            "F_P1": "P1_MainBooster",
            "S_P2": "P2_AuxBooster",
            "F_P2": "P2_AuxBooster",
            "S_V1": "V1_ZoneB_PRV",
            "P_PRV_INLET": "V1_ZoneB_PRV",
            "L_T1": "T1_Highlands",
            "L_T2": "T2_Eastside",
        }

    def attribute_incident(
        self,
        telemetry: pd.DataFrame,
        state_estimates: pd.DataFrame,
        sensor_trust: pd.DataFrame,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Ranks network components by suspicion score during anomalous periods."""
        # Find time steps where trust collapsed on any sensor (< 0.70)
        low_trust_mask = (sensor_trust < 0.70).any(axis=1)

        if not low_trust_mask.any():
            # If no obvious collapse, evaluate across all steps
            eval_steps = telemetry.index
        else:
            eval_steps = telemetry.index[low_trust_mask]

        scores: dict[str, float] = {}
        evidence: dict[str, list[str]] = {}

        for sensor_id, meta in self.sensors.items():
            if sensor_id not in telemetry.columns or sensor_id not in state_estimates.columns:
                continue

            y = telemetry.loc[eval_steps, sensor_id]
            x_hat = state_estimates.loc[eval_steps, sensor_id]
            t = sensor_trust.loc[eval_steps, sensor_id]

            # 1. Trust deficit: How severely did trust collapse?
            trust_deficit = (1.0 - t).mean() * 10.0

            # 2. Reconstruction residual: How far did reported telemetry diverge from physical state?
            nan_count = y.isna().sum()
            residual_mag = np.abs(y.fillna(x_hat) - x_hat).mean()
            norm_res = residual_mag / max(float(meta.noise_std), 0.1)

            # Combined sensor suspicion score
            sensor_score = trust_deficit + norm_res + (nan_count * 5.0)

            scores[sensor_id] = float(sensor_score)
            evidence[sensor_id] = [
                f"Mean trust: {t.mean():.2f}",
                f"State residual: {residual_mag:.2f} {meta.unit}",
            ]

            # If this sensor belongs to an actuator / tank element, credit the parent component too
            parent_element = self.element_mapping.get(sensor_id)
            if parent_element:
                if parent_element not in scores or sensor_score > scores[parent_element]:
                    scores[parent_element] = float(sensor_score * 1.05)
                    evidence[parent_element] = [
                        f"Associated sensor {sensor_id} degraded (trust: {t.mean():.2f})",
                        f"Discrepancy: {residual_mag:.2f} {meta.unit}",
                    ]

        # Sort components in descending order of suspicion
        sorted_components = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        results = []
        for comp_id, score in sorted_components[:top_k]:
            plc = self.sensors[comp_id].plc_id if comp_id in self.sensors else "PLANT_WIDE"
            results.append(
                {
                    "component_id": comp_id,
                    "plc_id": plc,
                    "suspicion_score": round(score, 2),
                    "evidence": evidence.get(comp_id, []),
                }
            )

        return results
