"""PROJECT LASTLINE: Physics-Constrained Hydraulic State Estimator.

Implements Weighted Least Squares (WLS) and Bayesian sensor fusion
guided by real-time telemetry trust weights and EPANET diurnal physical constraints.
"""

from typing import Any
import numpy as np
import pandas as pd

from backend.detection.trust_engine import TelemetryTrustEngine
from twin.model import WaterNetworkTwin
from twin.sensors import SensorType


class HydraulicStateEstimator:
    """Reconstructs the true physical state of the water network from untrusted telemetry."""

    def __init__(self, twin: WaterNetworkTwin, trust_engine: TelemetryTrustEngine, seed: int = 42):
        self.twin = twin
        self.trust_engine = trust_engine
        self.seed = seed
        self.sensors = twin.get_sensor_registry()
        self.sensor_keys = sorted(list(self.sensors.keys()))

        # Diurnal physical state prior statistics
        self.hourly_means: dict[str, pd.Series] = {}
        self.hourly_stds: dict[str, pd.Series] = {}
        self.sensor_noise_stds: dict[str, float] = {}
        self.is_fitted = False

    def fit_nominal(self, duration_hours: int = 72) -> None:
        """Fits prior hydraulic state distributions from nominal baseline simulation."""
        results = self.twin.simulate_baseline(duration_hours=duration_hours)
        df_nominal = self.twin.extract_telemetry(results, add_noise=True)

        hours = (df_nominal.index // 3600) % 24

        for col in self.sensor_keys:
            self.hourly_means[col] = df_nominal[col].groupby(hours).mean()
            # Empirical diurnal variance around the hourly mean
            std_s = df_nominal[col].groupby(hours).std().replace(0.0, 0.1)
            self.hourly_stds[col] = std_s.clip(lower=0.25)
            self.sensor_noise_stds[col] = max(float(self.sensors[col].noise_std), 0.05)

        self.is_fitted = True

    def reconstruct_state(self, telemetry: pd.DataFrame) -> dict[str, Any]:
        """Reconstructs true physical state x*(t) with uncertainty bounds."""
        if not self.is_fitted:
            self.fit_nominal()

        # Step 1: Evaluate real-time trust scores
        eval_result = self.trust_engine.evaluate_telemetry(telemetry)
        sensor_trust = eval_result["sensor_trust"]
        plc_trust = eval_result["plc_trust"]

        time_index = telemetry.index
        hours = (time_index // 3600) % 24

        state_estimates = pd.DataFrame(index=time_index, columns=self.sensor_keys, dtype=float)
        uncertainties = pd.DataFrame(index=time_index, columns=self.sensor_keys, dtype=float)

        for col in self.sensor_keys:
            meta = self.sensors[col]
            y = telemetry[col].values
            t_score = sensor_trust[col].values

            # Diurnal prior mean and variance
            prior_mu = np.array([self.hourly_means[col][h] for h in hours])
            prior_sigma = np.array([self.hourly_stds[col][h] for h in hours])
            prior_var = np.square(prior_sigma)

            # Measurement noise variance
            meas_sigma = self.sensor_noise_stds[col]
            meas_var = meas_sigma ** 2

            if meta.sensor_type in (SensorType.PUMP_STATUS, SensorType.VALVE_STATUS):
                # Status flags: if trust is high (>0.5), use reported; else fallback to prior expected status
                rec_status = np.where(t_score >= 0.5, y, np.round(prior_mu))
                # Replace NaNs
                rec_status = np.where(np.isnan(rec_status), np.round(prior_mu), rec_status)
                state_estimates[col] = rec_status
                uncertainties[col] = np.where(t_score >= 0.5, 0.05, 0.25)
                continue

            # Continuous measurements: WLS Bayesian fusion
            # Measurement precision weight scaled by trust score squared
            w_meas = np.square(t_score) / meas_var
            # Zero weight for missing/NaN telemetry
            w_meas = np.where(np.isnan(y), 0.0, w_meas)

            # Prior precision
            w_prior = 1.0 / prior_var

            # Posterior variance: 1 / (w_prior + w_meas)
            post_var = 1.0 / (w_prior + w_meas)
            post_std = np.sqrt(post_var)

            # Clean measurement values (NaN replaced with prior mean for arithmetic stability)
            y_clean = np.where(np.isnan(y), prior_mu, y)

            # Posterior mean
            post_mean = post_var * (w_prior * prior_mu + w_meas * y_clean)

            state_estimates[col] = post_mean
            uncertainties[col] = post_std

        return {
            "state_estimates": state_estimates,
            "uncertainties": uncertainties,
            "sensor_trust": sensor_trust,
            "plc_trust": plc_trust,
        }
