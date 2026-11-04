"""PROJECT LASTLINE: Water Network Digital Twin & Hydraulic Physics Engine.

Builds and simulates the Verdant City Water System (VCWS) benchmark model
using WNTR and EPANET, instrumenting physical components with PLC-mapped telemetry.
"""

from typing import Any

import numpy as np
import pandas as pd
import wntr

from twin.sensors import SensorMetadata, SensorType


class WaterNetworkTwin:
    """Digital Twin of the municipal water distribution and treatment network."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        self.model: wntr.network.WaterNetworkModel = self.build_network()
        self.sensors: dict[str, SensorMetadata] = self._register_sensors()

    def build_network(self) -> wntr.network.WaterNetworkModel:
        """Constructs the Verdant City water distribution network topology."""
        wn = wntr.network.WaterNetworkModel()
        wn.options.time.duration = 24 * 3600
        wn.options.time.hydraulic_timestep = 3600
        wn.options.time.report_timestep = 3600

        # Diurnal Demand Patterns
        # Residential pattern (morning peak 07:00-09:00, evening peak 18:00-20:00)
        res_pattern = [
            0.5,
            0.4,
            0.4,
            0.5,
            0.7,
            1.1,
            1.3,
            1.4,
            1.2,
            1.0,
            0.9,
            0.9,
            1.0,
            1.0,
            0.9,
            0.9,
            1.1,
            1.3,
            1.4,
            1.2,
            1.1,
            0.9,
            0.7,
            0.5,
        ]
        wn.add_pattern("pat_residential", res_pattern)

        # Commercial/Industrial pattern (steady daytime usage 08:00-18:00)
        ind_pattern = [
            0.4,
            0.4,
            0.4,
            0.5,
            0.7,
            1.0,
            1.2,
            1.3,
            1.3,
            1.3,
            1.2,
            1.2,
            1.2,
            1.2,
            1.1,
            1.1,
            1.0,
            0.8,
            0.6,
            0.5,
            0.4,
            0.4,
            0.4,
            0.4,
        ]
        wn.add_pattern("pat_industrial", ind_pattern)

        # Supply Reservoir (Elevation 10m, Base Head 25m)
        wn.add_reservoir("R1_Clearwell", base_head=25.0, coordinates=(0, 50))

        # Booster Pump Suction Node
        wn.add_junction("J0_PumpSuction", elevation=10.0, base_demand=0.0, coordinates=(5, 50))
        wn.add_pipe(
            "PIPE_SUCTION",
            "R1_Clearwell",
            "J0_PumpSuction",
            length=100.0,
            diameter=0.6,
            roughness=130,
        )

        # Booster Pump Discharge Node
        wn.add_junction("J0_Discharge", elevation=12.0, base_demand=0.0, coordinates=(15, 50))

        # Pump Head Curves
        wn.add_curve(
            "PUMP_CURVE_1", "HEAD", [(0.0, 85.0), (0.15, 75.0), (0.30, 62.0), (0.42, 45.0)]
        )
        wn.add_curve(
            "PUMP_CURVE_2", "HEAD", [(0.0, 80.0), (0.12, 70.0), (0.25, 58.0), (0.35, 42.0)]
        )

        # Pumps
        wn.add_pump(
            "P1_MainBooster",
            "J0_PumpSuction",
            "J0_Discharge",
            pump_type="HEAD",
            pump_parameter="PUMP_CURVE_1",
            initial_status="OPEN",
        )
        wn.add_pump(
            "P2_AuxBooster",
            "J0_PumpSuction",
            "J0_Discharge",
            pump_type="HEAD",
            pump_parameter="PUMP_CURVE_2",
            initial_status="CLOSED",
        )

        # Junctions: Zone A (North - Residential, Elevation 25-32m)
        wn.add_junction(
            "J1",
            elevation=25.0,
            base_demand=0.012,
            demand_pattern="pat_residential",
            coordinates=(30, 80),
        )
        wn.add_junction(
            "J2",
            elevation=28.0,
            base_demand=0.015,
            demand_pattern="pat_residential",
            coordinates=(50, 85),
        )
        wn.add_junction(
            "J3",
            elevation=30.0,
            base_demand=0.010,
            demand_pattern="pat_residential",
            coordinates=(70, 80),
        )
        wn.add_junction(
            "J4",
            elevation=32.0,
            base_demand=0.014,
            demand_pattern="pat_residential",
            coordinates=(50, 95),
        )

        # Elevated Storage Tank T1 (Zone A)
        wn.add_tank(
            "T1_Highlands",
            elevation=42.0,
            init_level=5.0,
            min_level=1.5,
            max_level=8.5,
            diameter=24.0,
            coordinates=(50, 110),
        )

        # Transmission Main to Zone A
        wn.add_pipe(
            "PIPE_TRANS_A", "J0_Discharge", "J1", length=600.0, diameter=0.45, roughness=130
        )

        # Distribution Mains: Zone A Grid
        wn.add_pipe("P_A1", "J1", "J2", length=300.0, diameter=0.30, roughness=120)
        wn.add_pipe("P_A2", "J2", "J3", length=350.0, diameter=0.30, roughness=120)
        wn.add_pipe("P_A3", "J1", "J4", length=400.0, diameter=0.30, roughness=120)
        wn.add_pipe("P_A4", "J4", "J2", length=300.0, diameter=0.25, roughness=120)
        wn.add_pipe("P_A_TANK", "J4", "T1_Highlands", length=200.0, diameter=0.35, roughness=130)

        # Junctions: Zone B (Central - Commercial/Civic, Elevation 15-20m)
        wn.add_junction("J_PRV_Inlet", elevation=18.0, base_demand=0.0, coordinates=(35, 50))
        wn.add_pipe(
            "PIPE_TRANS_B",
            "J0_Discharge",
            "J_PRV_Inlet",
            length=400.0,
            diameter=0.40,
            roughness=130,
        )

        wn.add_junction(
            "J5",
            elevation=18.0,
            base_demand=0.020,
            demand_pattern="pat_residential",
            coordinates=(45, 50),
        )
        wn.add_junction(
            "J6",
            elevation=16.0,
            base_demand=0.025,
            demand_pattern="pat_residential",
            coordinates=(65, 50),
        )
        wn.add_junction(
            "J7",
            elevation=15.0,
            base_demand=0.018,
            demand_pattern="pat_residential",
            coordinates=(65, 35),
        )
        wn.add_junction(
            "J8",
            elevation=19.0,
            base_demand=0.022,
            demand_pattern="pat_residential",
            coordinates=(45, 35),
        )

        # PRV Valve regulating downstream pressure to 28m head (~40 psi)
        wn.add_valve(
            "V1_ZoneB_PRV",
            "J_PRV_Inlet",
            "J5",
            diameter=0.30,
            valve_type="PRV",
            initial_setting=28.0,
            initial_status="ACTIVE",
        )

        # Distribution Mains: Zone B Grid
        wn.add_pipe("P_B1", "J5", "J6", length=400.0, diameter=0.30, roughness=120)
        wn.add_pipe("P_B2", "J6", "J7", length=350.0, diameter=0.25, roughness=120)
        wn.add_pipe("P_B3", "J7", "J8", length=400.0, diameter=0.25, roughness=120)
        wn.add_pipe("P_B4", "J8", "J5", length=350.0, diameter=0.25, roughness=120)

        # Junctions: Zone C (East - Industrial & Medical Center, Elevation 10-15m)
        wn.add_junction(
            "J9",
            elevation=12.0,
            base_demand=0.030,
            demand_pattern="pat_industrial",
            coordinates=(80, 50),
        )
        wn.add_junction(
            "J10",
            elevation=14.0,
            base_demand=0.035,
            demand_pattern="pat_industrial",
            coordinates=(100, 50),
        )
        wn.add_junction(
            "J11",
            elevation=11.0,
            base_demand=0.028,
            demand_pattern="pat_industrial",
            coordinates=(100, 30),
        )
        wn.add_junction(
            "J12",
            elevation=13.0,
            base_demand=0.032,
            demand_pattern="pat_industrial",
            coordinates=(80, 30),
        )

        # Elevated Storage Tank T2 (Zone C)
        wn.add_tank(
            "T2_Eastside",
            elevation=32.0,
            init_level=4.5,
            min_level=1.5,
            max_level=8.0,
            diameter=22.0,
            coordinates=(110, 40),
        )

        # Transmission Main to Zone C
        wn.add_pipe(
            "PIPE_TRANS_C", "J0_Discharge", "J9", length=900.0, diameter=0.45, roughness=130
        )

        # Distribution Mains: Zone C Grid
        wn.add_pipe("P_C1", "J9", "J10", length=450.0, diameter=0.35, roughness=120)
        wn.add_pipe("P_C2", "J10", "J11", length=400.0, diameter=0.30, roughness=120)
        wn.add_pipe("P_C3", "J11", "J12", length=450.0, diameter=0.30, roughness=120)
        wn.add_pipe("P_C4", "J12", "J9", length=400.0, diameter=0.30, roughness=120)
        wn.add_pipe("P_C_TANK", "J10", "T2_Eastside", length=250.0, diameter=0.35, roughness=130)

        # Inter-Zone Tie Line (between Zone B and Zone C)
        wn.add_pipe("P_INTER_BC", "J6", "J9", length=600.0, diameter=0.25, roughness=120)

        return wn

    def _register_sensors(self) -> dict[str, SensorMetadata]:
        """Instruments physical network elements with SCADA telemetry channels mapped to PLCs."""
        sensors = {}

        # PLC 1: Treatment Plant & Pump Station
        sensors["P_PUMP_SUCT"] = SensorMetadata(
            sensor_id="P_PUMP_SUCT",
            sensor_type=SensorType.JUNCTION_PRESSURE,
            element_id="J0_PumpSuction",
            plc_id="PLC_1",
            unit="m",
            min_normal=5.0,
            max_normal=25.0,
            criticality="high",
            zone_id="Treatment_Plant",
        )
        sensors["P_PUMP_DISCH"] = SensorMetadata(
            sensor_id="P_PUMP_DISCH",
            sensor_type=SensorType.JUNCTION_PRESSURE,
            element_id="J0_Discharge",
            plc_id="PLC_1",
            unit="m",
            min_normal=45.0,
            max_normal=85.0,
            criticality="critical",
            zone_id="Treatment_Plant",
        )
        sensors["F_P1"] = SensorMetadata(
            sensor_id="F_P1",
            sensor_type=SensorType.PIPE_FLOW,
            element_id="P1_MainBooster",
            plc_id="PLC_1",
            unit="m3/s",
            min_normal=0.0,
            max_normal=0.45,
            criticality="critical",
            zone_id="Treatment_Plant",
        )
        sensors["S_P1"] = SensorMetadata(
            sensor_id="S_P1",
            sensor_type=SensorType.PUMP_STATUS,
            element_id="P1_MainBooster",
            plc_id="PLC_1",
            unit="status",
            min_normal=0.0,
            max_normal=1.0,
            criticality="critical",
            zone_id="Treatment_Plant",
        )
        sensors["F_P2"] = SensorMetadata(
            sensor_id="F_P2",
            sensor_type=SensorType.PIPE_FLOW,
            element_id="P2_AuxBooster",
            plc_id="PLC_1",
            unit="m3/s",
            min_normal=0.0,
            max_normal=0.35,
            criticality="high",
            zone_id="Treatment_Plant",
        )
        sensors["S_P2"] = SensorMetadata(
            sensor_id="S_P2",
            sensor_type=SensorType.PUMP_STATUS,
            element_id="P2_AuxBooster",
            plc_id="PLC_1",
            unit="status",
            min_normal=0.0,
            max_normal=1.0,
            criticality="high",
            zone_id="Treatment_Plant",
        )

        # PLC 2: Zone A (North Highlands) & Tank 1
        sensors["L_T1"] = SensorMetadata(
            sensor_id="L_T1",
            sensor_type=SensorType.TANK_LEVEL,
            element_id="T1_Highlands",
            plc_id="PLC_2",
            unit="m",
            min_normal=1.5,
            max_normal=8.5,
            criticality="critical",
            zone_id="Zone_A_North",
        )
        for j_name, (min_p, max_p) in [
            ("J1", (20.0, 75.0)),
            ("J2", (18.0, 70.0)),
            ("J3", (15.0, 68.0)),
            ("J4", (15.0, 65.0)),
        ]:
            sensors[f"P_{j_name}"] = SensorMetadata(
                sensor_id=f"P_{j_name}",
                sensor_type=SensorType.JUNCTION_PRESSURE,
                element_id=j_name,
                plc_id="PLC_2",
                unit="m",
                min_normal=min_p,
                max_normal=max_p,
                criticality="medium",
                zone_id="Zone_A_North",
            )

        # PLC 3: Zone B (Central Commercial) & PRV Station
        sensors["P_PRV_INLET"] = SensorMetadata(
            sensor_id="P_PRV_INLET",
            sensor_type=SensorType.JUNCTION_PRESSURE,
            element_id="J_PRV_Inlet",
            plc_id="PLC_3",
            unit="m",
            min_normal=35.0,
            max_normal=75.0,
            criticality="high",
            zone_id="Zone_B_Central",
        )
        sensors["S_V1"] = SensorMetadata(
            sensor_id="S_V1",
            sensor_type=SensorType.VALVE_STATUS,
            element_id="V1_ZoneB_PRV",
            plc_id="PLC_3",
            unit="status",
            min_normal=0.0,
            max_normal=1.0,
            criticality="high",
            zone_id="Zone_B_Central",
        )
        for j_name, (min_p, max_p) in [
            ("J5", (15.0, 40.0)),
            ("J6", (15.0, 40.0)),
            ("J7", (15.0, 40.0)),
            ("J8", (15.0, 40.0)),
        ]:
            sensors[f"P_{j_name}"] = SensorMetadata(
                sensor_id=f"P_{j_name}",
                sensor_type=SensorType.JUNCTION_PRESSURE,
                element_id=j_name,
                plc_id="PLC_3",
                unit="m",
                min_normal=min_p,
                max_normal=max_p,
                criticality="medium",
                zone_id="Zone_B_Central",
            )

        # PLC 4: Zone C (Eastside Industrial) & Tank 2
        sensors["L_T2"] = SensorMetadata(
            sensor_id="L_T2",
            sensor_type=SensorType.TANK_LEVEL,
            element_id="T2_Eastside",
            plc_id="PLC_4",
            unit="m",
            min_normal=1.5,
            max_normal=8.0,
            criticality="critical",
            zone_id="Zone_C_Industrial",
        )
        for j_name, (min_p, max_p) in [
            ("J9", (25.0, 75.0)),
            ("J10", (22.0, 72.0)),
            ("J11", (25.0, 75.0)),
            ("J12", (22.0, 72.0)),
        ]:
            sensors[f"P_{j_name}"] = SensorMetadata(
                sensor_id=f"P_{j_name}",
                sensor_type=SensorType.JUNCTION_PRESSURE,
                element_id=j_name,
                plc_id="PLC_4",
                unit="m",
                min_normal=min_p,
                max_normal=max_p,
                criticality="medium",
                zone_id="Zone_C_Industrial",
            )

        return sensors

    def get_distribution_zones(self) -> dict[str, dict[str, Any]]:
        """Returns the operational zone partition and target service metrics."""
        return {
            "Zone_A_North": {
                "name": "North Highlands Residential",
                "junctions": ["J1", "J2", "J3", "J4"],
                "tank": "T1_Highlands",
                "target_pressure_min_m": 14.0,  # ~20 psi minimum regulatory service pressure
                "target_pressure_max_m": 60.0,
                "population_served": 28000,
                "critical_facilities": ["Highlands Senior Care", "North Elementary"],
            },
            "Zone_B_Central": {
                "name": "Central District Commercial & Civic",
                "junctions": ["J5", "J6", "J7", "J8"],
                "tank": None,
                "target_pressure_min_m": 15.0,
                "target_pressure_max_m": 40.0,
                "population_served": 42000,
                "critical_facilities": ["Municipal Hall", "Central Fire Station"],
            },
            "Zone_C_Industrial": {
                "name": "Eastside Industrial & Health Complex",
                "junctions": ["J9", "J10", "J11", "J12"],
                "tank": "T2_Eastside",
                "target_pressure_min_m": 20.0,
                "target_pressure_max_m": 65.0,
                "population_served": 19000,
                "critical_facilities": ["Regional Trauma Center", "BioTech Processing Campus"],
            },
        }

    def get_sensor_registry(self) -> dict[str, SensorMetadata]:
        """Returns the full dictionary of instrumented sensor channels."""
        return self.sensors

    def simulate_baseline(self, duration_hours: int = 24) -> wntr.sim.SimulationResults:
        """Simulates nominal hydraulics under diurnal demand patterns with zero attack perturbations."""
        wn = self.build_network()
        wn.options.time.duration = duration_hours * 3600
        wn.options.time.hydraulic_timestep = 3600
        wn.options.time.report_timestep = 3600

        sim = wntr.sim.EpanetSimulator(wn)
        results = sim.run_sim()
        return results

    def extract_telemetry(
        self, results: wntr.sim.SimulationResults, add_noise: bool = True
    ) -> pd.DataFrame:
        """Extracts clean or noise-corrupted sensor telemetry matrix from simulation results."""
        df_records = []
        timestamps = results.node["pressure"].index

        for t in timestamps:
            record: dict[str, Any] = {"timestamp": t}

            for sensor_id, meta in self.sensors.items():
                val: float = 0.0

                if meta.sensor_type == SensorType.TANK_LEVEL:
                    val = float(results.node["pressure"].loc[t, meta.element_id])
                elif meta.sensor_type == SensorType.JUNCTION_PRESSURE:
                    val = float(results.node["pressure"].loc[t, meta.element_id])
                elif meta.sensor_type == SensorType.PIPE_FLOW:
                    if meta.element_id in results.link["flowrate"].columns:
                        val = float(results.link["flowrate"].loc[t, meta.element_id])
                    else:
                        val = 0.0
                elif meta.sensor_type in (SensorType.PUMP_STATUS, SensorType.VALVE_STATUS):
                    if meta.element_id in results.link["status"].columns:
                        val = float(results.link["status"].loc[t, meta.element_id])
                    else:
                        val = 1.0

                if add_noise and meta.sensor_type not in (
                    SensorType.PUMP_STATUS,
                    SensorType.VALVE_STATUS,
                ):
                    noise = self._rng.normal(0.0, max(0.005 * abs(val), meta.noise_std))
                    val += noise

                record[sensor_id] = val

            df_records.append(record)

        return pd.DataFrame(df_records).set_index("timestamp")
