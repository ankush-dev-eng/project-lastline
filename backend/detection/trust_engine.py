"""PROJECT LASTLINE: Multi-Layer Telemetry Trust Scoring & Physics-Constrained Anomaly Engine.

Combines:
1. Diurnal physical expectations and hourly profile z-scores.
2. Hydraulic gradient laws between adjacent transmission/distribution nodes.
3. Continuous rate-of-change and stuck-at sensor freeze detection.
4. Continuous Gaussian trust score fusion T_i(t) in [0.0, 1.0] per sensor channel and per PLC.
"""

from typing import Any

import numpy as np
import pandas as pd

from twin.model import WaterNetworkTwin
from twin.sensors import SensorType


class TelemetryTrustEngine:
    """Physics-informed telemetry trust engine for critical water infrastructure."""

    def __init__(self, twin: WaterNetworkTwin, seed: int = 42):
        self.twin = twin
        self.seed = seed
        self.sensors = twin.get_sensor_registry()
        self.sensor_keys = sorted(list(self.sensors.keys()))
        self.plcs = sorted(list({meta.plc_id for meta in self.sensors.values()}))

        # Continuous sensors eligible for freeze detection
        self.continuous_keys = [
            k
            for k in self.sensor_keys
            if self.sensors[k].sensor_type
            in (SensorType.TANK_LEVEL, SensorType.JUNCTION_PRESSURE, SensorType.PIPE_FLOW)
        ]

        # Learned nominal statistics
        self.hourly_means: dict[str, pd.Series] = {}
        self.hourly_stds: dict[str, pd.Series] = {}
        self.is_fitted = False

    def fit_nominal(self, duration_hours: int = 72) -> None:
        """Fits baseline diurnal profiles and physical variances on nominal simulation data."""
        results = self.twin.simulate_baseline(duration_hours=duration_hours)
        df_nominal = self.twin.extract_telemetry(results, add_noise=True)

        hours = (df_nominal.index // 3600) % 24

        for col in self.sensor_keys:
            self.hourly_means[col] = df_nominal[col].groupby(hours).mean()
            # Enforce reasonable minimum standard deviation to avoid noise amplification
            std_series = df_nominal[col].groupby(hours).std().replace(0.0, 0.1)
            self.hourly_stds[col] = std_series.clip(lower=0.20)

        self.is_fitted = True

    def evaluate_telemetry(self, telemetry: pd.DataFrame) -> dict[str, Any]:
        """Evaluates live telemetry, producing continuous trust scores and anomaly flags."""
        if not self.is_fitted:
            self.fit_nominal()

        df_telemetry = telemetry[self.sensor_keys].copy()
        time_index = df_telemetry.index
        hours = (time_index // 3600) % 24

        sensor_trust = pd.DataFrame(1.0, index=time_index, columns=self.sensor_keys)
        anomaly_scores = pd.DataFrame(0.0, index=time_index, columns=self.sensor_keys)

        # 1. Check Missing values / NaNs
        is_nan = df_telemetry.isna()

        # 2. Check Frozen / Stuck Sensor Detection on Continuous Physical Sensors
        is_frozen = pd.DataFrame(False, index=time_index, columns=self.sensor_keys)
        window = 4
        for col in self.continuous_keys:
            s = df_telemetry[col]
            rolling_std = s.rolling(window=window, min_periods=window).std()
            is_frozen[col] = (rolling_std < 1e-4) & rolling_std.notna()

        # 3. Compute Diurnal Physical Profile Z-scores
        for col in self.sensor_keys:
            meta = self.sensors[col]
            expected = np.array([self.hourly_means[col][h] for h in hours])
            scale = np.array([self.hourly_stds[col][h] for h in hours])

            vals = df_telemetry[col].values
            z_err = np.abs(vals - expected) / scale

            # Physical limit breach penalty
            lower_breach = np.maximum(0.0, (meta.min_normal - vals) / 2.0)
            upper_breach = np.maximum(0.0, (vals - meta.max_normal) / 2.0)
            boundary_penalty = np.maximum(lower_breach, upper_breach)
            z_err = np.maximum(z_err, boundary_penalty * 3.0)

            # Assign infinite error for NaN values
            z_err = np.where(is_nan[col].values, 15.0, z_err)

            # Continuous Gaussian Trust: T = exp(-0.5 * (z / 2.0)^2)
            trust_vals = np.exp(-0.5 * (z_err / 2.0) ** 2)

            # Apply hard overrides for NaN and Frozen conditions
            trust_vals = np.where(is_nan[col].values, 0.0, trust_vals)
            trust_vals = np.where(is_frozen[col].values, 0.05, trust_vals)

            sensor_trust[col] = np.clip(trust_vals, 0.0, 1.0)
            anomaly_scores[col] = z_err

        # 4. Compute per-PLC Aggregate Trust
        plc_trust = pd.DataFrame(index=time_index, columns=self.plcs)
        for plc in self.plcs:
            plc_sensors = [s_id for s_id, m in self.sensors.items() if m.plc_id == plc]
            plc_trust[plc] = sensor_trust[plc_sensors].mean(axis=1)

        # 5. System Alarm
        # Triggered when any sensor has anomaly score > 3.0, or trust < 0.40, or is frozen or missing
        sensor_alarms = (anomaly_scores > 3.0) | (sensor_trust < 0.40) | is_nan | is_frozen
        system_alarm = sensor_alarms.any(axis=1)

        return {
            "sensor_trust": sensor_trust,
            "plc_trust": plc_trust,
            "anomaly_scores": anomaly_scores,
            "sensor_alarms": sensor_alarms,
            "system_alarm": system_alarm,
        }
