"""PROJECT LASTLINE: Multi-Layer Telemetry Trust Scoring & Physics-Constrained Anomaly Engine.

Combines:
1. Physical continuity, rate-of-change, and hydraulic gradient laws.
2. Principal Component Analysis (PCA) subspace reconstruction residuals.
3. Continuous trust score fusion T_i(t) in [0.0, 1.0] per sensor channel and per PLC.
"""

from typing import Any
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

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

        # Hydraulic neighbor pairs for gradient consistency checks
        self.gradient_pairs = [
            ("P_J1", "P_J2"),
            ("P_J2", "P_J3"),
            ("P_J3", "P_J4"),
            ("P_J5", "P_J6"),
            ("P_J6", "P_J7"),
            ("P_J7", "P_J8"),
            ("P_J9", "P_J10"),
            ("P_J10", "P_J11"),
            ("P_J11", "P_J12"),
            ("P_PRV_INLET", "P_J5"),
        ]

        # Learned nominal statistics
        self.means: pd.Series | None = None
        self.stds: pd.Series | None = None
        self.pca: PCA | None = None
        self.pca_thresholds: dict[str, float] = {}
        self.gradient_means: dict[tuple[str, str], float] = {}
        self.gradient_stds: dict[tuple[str, str], float] = {}
        self.is_fitted = False

    def fit_nominal(self, duration_hours: int = 72) -> None:
        """Fits baseline multivariate subspace and hydraulic constraints on nominal simulation data."""
        # Generate 72 hours of nominal diurnal operations with realistic instrumentation noise
        results = self.twin.simulate_baseline(duration_hours=duration_hours)
        df_nominal = self.twin.extract_telemetry(results, add_noise=True)

        # 1. Compute per-sensor nominal mean and standard deviation
        self.means = df_nominal[self.sensor_keys].mean()
        self.stds = df_nominal[self.sensor_keys].std()
        # Avoid division by zero on static status flags
        self.stds = self.stds.replace(0.0, 1.0)

        # Standardized matrix
        z_nominal = (df_nominal[self.sensor_keys] - self.means) / self.stds

        # 2. Fit PCA on nominal diurnal patterns (k=4 principal components capture >95% diurnal variance)
        self.pca = PCA(n_components=min(5, len(self.sensor_keys)), random_state=self.seed)
        self.pca.fit(z_nominal)

        # Project and compute reconstruction residuals under nominal conditions
        z_reconstructed = self.pca.inverse_transform(self.pca.transform(z_nominal))
        residuals = np.abs(z_nominal.values - z_reconstructed)

        # Threshold set at 98.5th percentile of nominal residuals per sensor + safe margin
        for idx, col in enumerate(self.sensor_keys):
            q98 = np.percentile(residuals[:, idx], 98.5)
            self.pca_thresholds[col] = max(float(q98 * 1.4), 0.75)

        # 3. Fit hydraulic gradient statistics between adjacent nodes
        for s1, s2 in self.gradient_pairs:
            if s1 in df_nominal.columns and s2 in df_nominal.columns:
                diff = df_nominal[s1] - df_nominal[s2]
                self.gradient_means[(s1, s2)] = float(diff.mean())
                self.gradient_stds[(s1, s2)] = max(float(diff.std()), 0.25)

        self.is_fitted = True

    def evaluate_telemetry(self, telemetry: pd.DataFrame) -> dict[str, Any]:
        """Evaluates live telemetry, producing continuous trust scores and anomaly flags."""
        if not self.is_fitted:
            self.fit_nominal()

        df_telemetry = telemetry[self.sensor_keys].copy()
        n_steps = len(df_telemetry)
        time_index = df_telemetry.index

        # Initialize trust scores matrix
        sensor_trust = pd.DataFrame(1.0, index=time_index, columns=self.sensor_keys)
        anomaly_scores = pd.DataFrame(0.0, index=time_index, columns=self.sensor_keys)

        # Check 1: Missing values / NaNs (Communication Loss / Dropout)
        is_nan = df_telemetry.isna()

        # Check 2: Frozen / Stuck Sensor Detection
        is_frozen = pd.DataFrame(False, index=time_index, columns=self.sensor_keys)
        window = 4
        for col in self.sensor_keys:
            meta = self.sensors[col]
            if meta.sensor_type not in (SensorType.PUMP_STATUS, SensorType.VALVE_STATUS):
                rolling_std = df_telemetry[col].rolling(window=window, min_periods=window).std()
                # If rolling std is zero while the sensor is continuous, it is frozen
                is_frozen[col] = (rolling_std < 1e-4) & (rolling_std.notna())

        # Check 3: Multivariate PCA Reconstruction Residuals
        # Impute NaNs with nominal means for projection
        imputed_data = df_telemetry.fillna(self.means)
        z_norm = (imputed_data - self.means) / self.stds
        z_proj = self.pca.inverse_transform(self.pca.transform(z_norm))
        pca_residuals = np.abs(z_norm.values - z_proj)
        df_pca_res = pd.DataFrame(pca_residuals, index=time_index, columns=self.sensor_keys)

        # Check 4: Hydraulic Gradient Residuals
        grad_residuals = {col: np.zeros(n_steps) for col in self.sensor_keys}
        for (s1, s2), mean_diff in self.gradient_means.items():
            std_diff = self.gradient_stds[(s1, s2)]
            if s1 in df_telemetry.columns and s2 in df_telemetry.columns:
                actual_diff = df_telemetry[s1] - df_telemetry[s2]
                grad_err = (np.abs(actual_diff - mean_diff) / std_diff).fillna(0.0).values
                # Assign gradient discrepancy to both interconnected sensors
                grad_residuals[s1] = np.maximum(grad_residuals[s1], grad_err)
                grad_residuals[s2] = np.maximum(grad_residuals[s2], grad_err)

        # Check 5: Hard Upper/Lower Physical Boundary Residuals
        for col in self.sensor_keys:
            meta = self.sensors[col]
            series = df_telemetry[col]
            pca_err = df_pca_res[col].values / self.pca_thresholds[col]
            grad_err = grad_residuals[col] / 2.8

            # Combine anomaly signals
            combined_err = np.maximum(pca_err, grad_err)

            # Physical limit breach penalty
            lower_breach = np.maximum(0.0, (meta.min_normal - series) / (0.15 * meta.min_normal + 1.0)).fillna(0.0)
            upper_breach = np.maximum(0.0, (series - meta.max_normal) / (0.15 * meta.max_normal + 1.0)).fillna(0.0)
            boundary_err = np.maximum(lower_breach, upper_breach)
            total_err = np.maximum(combined_err, boundary_err * 2.0)

            # Continuous Gaussian Trust Transformation: T = exp(-0.5 * (err/1.2)^2)
            trust_vals = np.exp(-0.5 * (total_err / 1.15) ** 2)

            # Apply hard overrides for NaN and Frozen conditions
            trust_vals = np.where(is_nan[col].values, 0.0, trust_vals)
            trust_vals = np.where(is_frozen[col].values, 0.05, trust_vals)

            sensor_trust[col] = np.clip(trust_vals, 0.0, 1.0)
            anomaly_scores[col] = total_err

        # Compute per-PLC Aggregate Trust
        plc_trust = pd.DataFrame(index=time_index, columns=self.plcs)
        for plc in self.plcs:
            plc_sensors = [s_id for s_id, m in self.sensors.items() if m.plc_id == plc]
            plc_trust[plc] = sensor_trust[plc_sensors].mean(axis=1)

        # System Alarm triggered when minimum sensor trust falls below 0.48 or any anomaly score > 2.2
        sensor_alarms = (sensor_trust < 0.48) | (anomaly_scores > 2.2) | is_nan | is_frozen
        system_alarm = sensor_alarms.any(axis=1)

        return {
            "sensor_trust": sensor_trust,
            "plc_trust": plc_trust,
            "anomaly_scores": anomaly_scores,
            "sensor_alarms": sensor_alarms,
            "system_alarm": system_alarm,
        }
