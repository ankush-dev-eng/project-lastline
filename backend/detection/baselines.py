"""PROJECT LASTLINE: Naive Baseline Detectors for Honest Evaluation Benchmarks.

Implements standard industry baselines:
1. Raw Telemetry Trust (Trust = 1.0 unconditionally)
2. Fixed Static Threshold Alarm (Alarms only if sensor breaches preset min/max bounds)
"""

from typing import Any
import pandas as pd

from twin.model import WaterNetworkTwin


class FixedThresholdDetector:
    """Conventional SCADA alarm baseline: triggers alarm only on static upper/lower threshold breaches."""

    def __init__(self, twin: WaterNetworkTwin):
        self.twin = twin
        self.sensors = twin.get_sensor_registry()

    def evaluate_telemetry(self, telemetry: pd.DataFrame) -> dict[str, Any]:
        """Evaluates telemetry using static high/low limits from sensor metadata."""
        n_steps = len(telemetry)
        sensor_trust = pd.DataFrame(index=telemetry.index)
        sensor_alarms = pd.DataFrame(index=telemetry.index)

        for sensor_id, meta in self.sensors.items():
            if sensor_id not in telemetry.columns:
                sensor_trust[sensor_id] = 0.0
                sensor_alarms[sensor_id] = True
                continue

            series = telemetry[sensor_id]
            is_nan = series.isna()
            out_of_bounds = (series < meta.min_normal) | (series > meta.max_normal)
            alarmed = is_nan | out_of_bounds

            sensor_alarms[sensor_id] = alarmed
            # Naive binary trust: 1.0 if inside normal bounds, 0.0 if breached
            sensor_trust[sensor_id] = (~alarmed).astype(float)

        system_alarm = sensor_alarms.any(axis=1)

        # Aggregate PLC trust
        plc_trust = pd.DataFrame(index=telemetry.index)
        plcs = {meta.plc_id for meta in self.sensors.values()}
        for plc in plcs:
            plc_sensors = [s_id for s_id, m in self.sensors.items() if m.plc_id == plc]
            plc_trust[plc] = sensor_trust[plc_sensors].mean(axis=1)

        return {
            "sensor_trust": sensor_trust,
            "plc_trust": plc_trust,
            "sensor_alarms": sensor_alarms,
            "system_alarm": system_alarm,
        }
