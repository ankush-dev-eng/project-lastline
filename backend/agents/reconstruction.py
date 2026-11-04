"""PROJECT LASTLINE: Reconstruction Physical State Agent.

Reconstructs the true physical state of the water distribution network
from untrusted telemetry using physics constraints, diurnal priors, and Bayesian fusion.
"""

import time

import numpy as np
import pandas as pd

from backend.agents.contracts import IntegrityReport, ReconstructionReport
from backend.reconstruction.attribution import ComponentAttributionEngine
from backend.reconstruction.estimator import HydraulicStateEstimator


class ReconstructionAgent:
    """Specialized agent orchestrating hydraulic state estimation and component attribution."""

    def __init__(
        self,
        estimator: HydraulicStateEstimator,
        attribution_engine: ComponentAttributionEngine,
    ):
        self.estimator = estimator
        self.attribution_engine = attribution_engine

    def reconstruct(
        self,
        telemetry: pd.DataFrame,
        integrity_report: IntegrityReport | None = None,
        timestep_idx: int | None = None,
    ) -> ReconstructionReport:
        """Reconstructs true physical state and quantifies epistemic uncertainty."""
        recon_result = self.estimator.reconstruct_state(telemetry)

        state_df = recon_result["state_estimates"]
        unc_df = recon_result["uncertainties"]
        trust_df = recon_result["sensor_trust"]

        # Timestep selection
        if timestep_idx is not None:
            eval_idx = timestep_idx
        elif integrity_report and integrity_report.system_alarm:
            min_trusts = trust_df.min(axis=1)
            eval_idx = int(min_trusts.argmin())
        else:
            eval_idx = -1

        latest_estimates = {col: float(state_df[col].iloc[eval_idx]) for col in state_df.columns}
        latest_uncertainties = {col: float(unc_df[col].iloc[eval_idx]) for col in unc_df.columns}

        # Attribution ranking
        ranked_components = self.attribution_engine.attribute_incident(
            telemetry=telemetry,
            state_estimates=state_df,
            sensor_trust=trust_df,
            top_k=5,
        )

        # Compute overall stability index based on trust scores and residual deviations
        mean_trust = float(np.mean(list(trust_df.iloc[eval_idx].values)))
        stability_index = float(np.clip(mean_trust, 0.0, 1.0))

        return ReconstructionReport(
            stability_index=stability_index,
            top_suspicious_components=ranked_components,
            state_estimates=latest_estimates,
            uncertainties=latest_uncertainties,
            timestamp=time.time(),
        )
