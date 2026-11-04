"""PROJECT LASTLINE: Integrity Telemetry Trust Agent.

Assesses physical plausibility, rate-of-change, and correlation residuals
to score real-time trust for individual sensors and PLCs.
"""

import time

import numpy as np
import pandas as pd

from backend.agents.contracts import IntegrityReport, SentinelReport
from backend.detection.trust_engine import TelemetryTrustEngine


class IntegrityAgent:
    """Specialized agent evaluating physical telemetry consistency and scoring trust."""

    def __init__(self, trust_engine: TelemetryTrustEngine):
        self.trust_engine = trust_engine

    def evaluate(
        self,
        telemetry: pd.DataFrame,
        sentinel_report: SentinelReport | None = None,
        timestep_idx: int | None = None,
    ) -> IntegrityReport:
        """Evaluates telemetry matrix against physical diurnal constraints and cyber alerts."""
        eval_result = self.trust_engine.evaluate_telemetry(telemetry)

        # Select evaluation timestep: explicit index, peak incident timestep, or latest
        if timestep_idx is not None:
            eval_idx = timestep_idx
        elif eval_result["system_alarm"].any():
            alarm_indices = np.where(eval_result["system_alarm"])[0]
            min_trusts = eval_result["sensor_trust"].iloc[alarm_indices].min(axis=1)
            eval_idx = int(alarm_indices[min_trusts.argmin()])
        else:
            eval_idx = -1

        sensor_trust_latest = {
            col: float(eval_result["sensor_trust"][col].iloc[eval_idx])
            for col in eval_result["sensor_trust"].columns
        }
        plc_trust_latest = {
            plc: float(eval_result["plc_trust"][plc].iloc[eval_idx])
            for plc in eval_result["plc_trust"].columns
        }

        # If Sentinel flagged specific PLCs as under cyber attack, down-weight those PLCs
        if sentinel_report and sentinel_report.flagged_plcs:
            for plc in sentinel_report.flagged_plcs:
                if plc in plc_trust_latest:
                    plc_trust_latest[plc] = min(plc_trust_latest[plc], 0.35)

        # Identify compromised sensors (trust score < 0.50)
        compromised = [
            sensor_id for sensor_id, trust_val in sensor_trust_latest.items() if trust_val < 0.50
        ]

        system_alarm = bool(
            eval_result["system_alarm"].any()
            or len(compromised) > 0
            or (sentinel_report and bool(sentinel_report.flagged_plcs))
        )

        return IntegrityReport(
            system_alarm=system_alarm,
            compromised_sensors=sorted(compromised),
            sensor_trust=sensor_trust_latest,
            plc_trust=plc_trust_latest,
            timestamp=time.time(),
        )
