"""PROJECT LASTLINE: Digital Twin Playbook Pre-Simulation Engine.

Clones the EPANET water network model and simulates hypothetical emergency interventions forward
in time to verify that minimum junction pressures and tank storage envelopes are strictly preserved.
"""

import time

import wntr
from pydantic import BaseModel, Field

from backend.playbooks.catalog import FallbackPlaybook
from twin.model import WaterNetworkTwin


class SimulationVerificationResult(BaseModel):
    playbook_id: str
    is_valid: bool
    min_pressure_observed_m: float
    min_tank_levels: dict[str, float] = Field(default_factory=dict)
    max_tank_levels: dict[str, float] = Field(default_factory=dict)
    constraint_violations: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0


class TwinPlaybookSimulator:
    """Simulates operational fallback playbooks inside the EPANET digital twin before display."""

    def __init__(self, twin: WaterNetworkTwin):
        self.twin = twin

    def simulate_playbook(
        self,
        playbook: FallbackPlaybook,
        duration_hours: int = 24,
    ) -> SimulationVerificationResult:
        """Simulates candidate playbook in a sandbox clone of the network model."""
        t0 = time.perf_counter()

        # Build fresh isolated clone of the network
        wn = self.twin.build_network()
        wn.options.time.duration = duration_hours * 3600
        wn.options.time.hydraulic_timestep = 3600
        wn.options.time.report_timestep = 3600

        # Apply interventions
        for interv in playbook.interventions:
            elem_id = interv.element_id
            param = interv.parameter
            val = interv.target_value

            if interv.element_type == "pump":
                pump = wn.get_link(elem_id)
                if param == "status":
                    pump.initial_status = str(val)
                elif param == "setting":
                    pump.initial_setting = float(val)

            elif interv.element_type == "valve":
                valve = wn.get_link(elem_id)
                if param == "status":
                    valve.initial_status = str(val)
                elif param == "setting":
                    valve.initial_setting = float(val)

            elif interv.element_type == "pipe":
                pipe = wn.get_link(elem_id)
                if param == "status":
                    pipe.initial_status = str(val)

            elif interv.element_type == "junction":
                junc = wn.get_node(elem_id)
                if param == "base_demand":
                    junc.base_demand = float(val)

        # Run EPANET hydraulic simulation
        sim = wntr.sim.EpanetSimulator(wn)
        try:
            results = sim.run_sim()
        except Exception as e:
            t1 = time.perf_counter()
            return SimulationVerificationResult(
                playbook_id=playbook.playbook_id,
                is_valid=False,
                min_pressure_observed_m=-99.0,
                min_tank_levels={},
                max_tank_levels={},
                constraint_violations=[f"EPANET simulation failed with error: {str(e)}"],
                execution_time_ms=(t1 - t0) * 1000.0,
            )

        # Evaluate physical constraints
        violations: list[str] = []

        # 1. Minimum Junction Pressure constraint (Customer delivery P >= 15.0m, Suction P > 0m)
        customer_juncs = [j for j in wn.junction_name_list if "Suction" not in j]
        p_customer = results.node["pressure"].loc[:, customer_juncs]
        min_p = float(p_customer.min().min())

        if min_p < 15.0:
            violations.append(
                f"Minimum customer delivery junction pressure {min_p:.2f}m is below required 15.0m head threshold."
            )

        suction_juncs = [j for j in wn.junction_name_list if "Suction" in j]
        if suction_juncs:
            min_suct = float(results.node["pressure"].loc[:, suction_juncs].min().min())
            if min_suct <= 0.0:
                violations.append(
                    f"Suction node cavitated with negative pressure {min_suct:.2f}m."
                )

        # 2. Tank Storage Level Envelope constraints (1.5m <= L <= 9.0m)
        tank_names = list(wn.tank_name_list)
        min_tank_levels: dict[str, float] = {}
        max_tank_levels: dict[str, float] = {}

        for tank_name in tank_names:
            lvl_series = results.node["pressure"].loc[:, tank_name]
            min_l = float(lvl_series.min())
            max_l = float(lvl_series.max())
            min_tank_levels[tank_name] = round(min_l, 2)
            max_tank_levels[tank_name] = round(max_l, 2)

            if min_l < 1.5:
                violations.append(
                    f"Tank '{tank_name}' depleted to {min_l:.2f}m, below minimum operating limit 1.5m."
                )
            if max_l > 9.0:
                violations.append(
                    f"Tank '{tank_name}' overflow risk at {max_l:.2f}m, above maximum operating limit 9.0m."
                )

        t1 = time.perf_counter()
        is_valid = len(violations) == 0

        return SimulationVerificationResult(
            playbook_id=playbook.playbook_id,
            is_valid=is_valid,
            min_pressure_observed_m=round(min_p, 2),
            min_tank_levels=min_tank_levels,
            max_tank_levels=max_tank_levels,
            constraint_violations=violations,
            execution_time_ms=round((t1 - t0) * 1000.0, 2),
        )
