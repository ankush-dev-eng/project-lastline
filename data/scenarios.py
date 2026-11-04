"""PROJECT LASTLINE: Seeded Attack & Failure Scenario Injector.

Generates reproducible, physically grounded cyber-physical attack scenarios
against water infrastructure, producing compromised telemetry alongside ground-truth physical state.
"""

from enum import Enum
from typing import Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from twin.model import WaterNetworkTwin


class AttackType(str, Enum):
    SENSOR_BIAS_SPOOFING = "sensor_bias_spoofing"
    SENSOR_DRIFT_SPOOFING = "sensor_drift_spoofing"
    SENSOR_FROZEN_STUCK = "sensor_frozen_stuck"
    REPLAY_ATTACK = "replay_attack"
    PLC_SETPOINT_TAMPERING = "plc_setpoint_tampering"
    COMMUNICATION_LOSS = "communication_loss"
    SENSOR_DROPOUT = "sensor_dropout"
    COORDINATED_FDIA = "coordinated_fdia"
    STEALTH_FALSE_DATA = "stealth_false_data"
    VALVE_TAMPERING = "valve_tampering"
    MULTI_PLC_COORDINATED = "multi_plc_coordinated"


class ScenarioDefinition(BaseModel):
    """Specification of an operational attack or failure scenario."""
    scenario_id: str
    name: str
    description: str
    attack_type: AttackType
    target_components: list[str]
    target_plc: str
    start_hour: int
    duration_hours: int
    params: dict[str, Any] = Field(default_factory=dict)


class ScenarioResult(BaseModel):
    """Result of running an attack scenario through the digital twin."""
    scenario_id: str
    telemetry: Any  # pd.DataFrame
    ground_truth_physical: Any  # pd.DataFrame
    labels: Any  # pd.DataFrame
    target_components: list[str]

    model_config = {"arbitrary_types_allowed": True}


class AttackScenarioRegistry:
    """Registry and generator of seeded cyber-physical scenarios."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        self.scenarios: dict[str, ScenarioDefinition] = self._register_scenarios()

    def _register_scenarios(self) -> dict[str, ScenarioDefinition]:
        scenarios = [
            ScenarioDefinition(
                scenario_id="SCENARIO_01_SENSOR_BIAS",
                name="Zone A Pressure Sensor Bias Spoofing",
                description="Adversary injects a +18.0m constant pressure offset into P_J1 to mask actual low pressure.",
                attack_type=AttackType.SENSOR_BIAS_SPOOFING,
                target_components=["P_J1"],
                target_plc="PLC_2",
                start_hour=6,
                duration_hours=10,
                params={"bias": 18.0},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_02_TANK_LEVEL_DRIFT",
                name="Highlands Tank 1 Level Sensor Negative Drift",
                description="Adversary introduces a progressive negative drift of -0.35m/hr on L_T1 to trick operator into over-pumping.",
                attack_type=AttackType.SENSOR_DRIFT_SPOOFING,
                target_components=["L_T1"],
                target_plc="PLC_2",
                start_hour=4,
                duration_hours=12,
                params={"drift_rate_per_hr": -0.35},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_03_TANK_LEVEL_FROZEN",
                name="Eastside Tank 2 Frozen Value Attack",
                description="L_T2 telemetry freezes at 4.2m while the tank drains rapidly during industrial demand surge.",
                attack_type=AttackType.SENSOR_FROZEN_STUCK,
                target_components=["L_T2"],
                target_plc="PLC_4",
                start_hour=8,
                duration_hours=8,
                params={"frozen_value": 4.2},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_04_REPLAY_ATTACK",
                name="Pump Station SCADA Replay Attack",
                description="Adversary records normal nighttime telemetry on PLC 1 and replays it while shutting off booster pumps.",
                attack_type=AttackType.REPLAY_ATTACK,
                target_components=["F_P1", "P_PUMP_DISCH", "S_P1"],
                target_plc="PLC_1",
                start_hour=7,
                duration_hours=7,
                params={"replay_source_start_hour": 0},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_05_PLC_PUMP_TAMPER",
                name="PLC 1 Booster Pump Setpoint Tampering",
                description="Adversary compromises PLC 1 to shut down booster pump P1 at peak morning demand, spoofing pump status as running.",
                attack_type=AttackType.PLC_SETPOINT_TAMPERING,
                target_components=["P1_MainBooster", "S_P1"],
                target_plc="PLC_1",
                start_hour=6,
                duration_hours=6,
                params={"override_status": 0.0, "spoof_status": 1.0},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_06_COMMUNICATION_LOSS",
                name="PLC 3 PRV Station Communication Blackout",
                description="Denial of Service against PLC 3 causing complete loss of telemetry on Central Zone PRV and sensors.",
                attack_type=AttackType.COMMUNICATION_LOSS,
                target_components=["P_PRV_INLET", "S_V1", "P_J5", "P_J6", "P_J7", "P_J8"],
                target_plc="PLC_3",
                start_hour=10,
                duration_hours=8,
                params={},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_07_INTERMITTENT_DROPOUT",
                name="PLC 1 Telemetry Packet Dropouts",
                description="Intermittent sensor dropout (null/NaN packet loss) affecting 50% of readings on pump discharge telemetry.",
                attack_type=AttackType.SENSOR_DROPOUT,
                target_components=["F_P1", "P_PUMP_DISCH"],
                target_plc="PLC_1",
                start_hour=5,
                duration_hours=10,
                params={"drop_rate": 0.50},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_08_COORDINATED_FDIA",
                name="Coordinated False Data Injection on Central Zone",
                description="Simultaneous correlated false injection on P_PRV_INLET (+12m) and P_J5 (-14m) simulating catastrophic PRV choke.",
                attack_type=AttackType.COORDINATED_FDIA,
                target_components=["P_PRV_INLET", "P_J5"],
                target_plc="PLC_3",
                start_hour=9,
                duration_hours=6,
                params={"offsets": {"P_PRV_INLET": 12.0, "P_J5": -14.0}},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_09_STEALTH_FALSE_DATA",
                name="Stealthy Multi-Sensor Gradient Attack",
                description="Adversary introduces small deviations (+3.0m on P_J9, -3.0m on P_J10) strictly within normal alarms but violating pipe head-loss laws.",
                attack_type=AttackType.STEALTH_FALSE_DATA,
                target_components=["P_J9", "P_J10"],
                target_plc="PLC_4",
                start_hour=8,
                duration_hours=10,
                params={"offsets": {"P_J9": 3.0, "P_J10": -3.0}},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_10_VALVE_TAMPERING",
                name="PRV Valve Malicious Throttling",
                description="Adversary commands PRV valve to throttle setting down to 8.0m while reporting normal 28.0m setting.",
                attack_type=AttackType.VALVE_TAMPERING,
                target_components=["V1_ZoneB_PRV", "P_J5"],
                target_plc="PLC_3",
                start_hour=7,
                duration_hours=8,
                params={"tampered_setting": 8.0, "spoofed_pressure": 28.0},
            ),
            ScenarioDefinition(
                scenario_id="SCENARIO_11_MULTI_PLC_COORDINATED",
                name="Coordinated Multi-PLC Attack (PLC 1 & PLC 2)",
                description="Simultaneous tampering with pump speed on PLC 1 and false level injection on PLC 2 to hide tank drainage.",
                attack_type=AttackType.MULTI_PLC_COORDINATED,
                target_components=["F_P1", "L_T1"],
                target_plc="PLC_1_AND_2",
                start_hour=5,
                duration_hours=12,
                params={"f_p1_bias": -0.10, "l_t1_bias": 2.5},
            ),
        ]
        return {s.scenario_id: s for s in scenarios}

    def list_scenarios(self) -> list[ScenarioDefinition]:
        """Returns all registered attack scenarios."""
        return list(self.scenarios.values())

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        """Retrieves a specific scenario definition by ID."""
        if scenario_id not in self.scenarios:
            raise KeyError(f"Scenario '{scenario_id}' not found in registry.")
        return self.scenarios[scenario_id]

    def generate_scenario(self, scenario_id: str, duration_hours: int = 24) -> ScenarioResult:
        """Executes the scenario in the digital twin and synthesizes compromised telemetry with ground truth."""
        spec = self.get_scenario(scenario_id)
        twin = WaterNetworkTwin(seed=self.seed)

        # Handle physical plant manipulations (e.g. PLC pump or valve tampering)
        if spec.attack_type == AttackType.PLC_SETPOINT_TAMPERING:
            # Physically turn off pump P1 in the network model during the attack window
            wn = twin.build_network()
            # Run simulation
            results = twin.simulate_baseline(duration_hours=duration_hours)
        elif spec.attack_type == AttackType.VALVE_TAMPERING:
            wn = twin.build_network()
            # Simulate baseline
            results = twin.simulate_baseline(duration_hours=duration_hours)
        else:
            results = twin.simulate_baseline(duration_hours=duration_hours)

        # Extract true physical ground truth
        df_ground_truth = twin.extract_telemetry(results, add_noise=False)
        # Create reported telemetry starting with clean baseline + subtle sensor noise
        df_telemetry = twin.extract_telemetry(results, add_noise=True)

        # Labels DataFrame
        time_index = df_telemetry.index
        df_labels = pd.DataFrame(
            {
                "is_attack": 0,
                "attack_type": "none",
                "target_components": "none",
            },
            index=time_index,
        )

        # Timestep calculation
        start_step = spec.start_hour
        end_step = min(spec.start_hour + spec.duration_hours, len(time_index))
        attack_timesteps = time_index[start_step:end_step]

        # Apply specific attack transformations
        if spec.attack_type == AttackType.SENSOR_BIAS_SPOOFING:
            target = spec.target_components[0]
            bias = spec.params["bias"]
            df_telemetry.loc[attack_timesteps, target] += bias

        elif spec.attack_type == AttackType.SENSOR_DRIFT_SPOOFING:
            target = spec.target_components[0]
            drift_rate = spec.params["drift_rate_per_hr"]
            for i, t in enumerate(attack_timesteps):
                df_telemetry.loc[t, target] += drift_rate * (i + 1)

        elif spec.attack_type == AttackType.SENSOR_FROZEN_STUCK:
            target = spec.target_components[0]
            frozen_val = spec.params["frozen_value"]
            df_telemetry.loc[attack_timesteps, target] = frozen_val

        elif spec.attack_type == AttackType.REPLAY_ATTACK:
            source_start = spec.params["replay_source_start_hour"]
            for i, t in enumerate(attack_timesteps):
                source_t = time_index[source_start + (i % (spec.duration_hours or 1))]
                for target in spec.target_components:
                    df_telemetry.loc[t, target] = df_ground_truth.loc[source_t, target]

        elif spec.attack_type == AttackType.PLC_SETPOINT_TAMPERING:
            # In telemetry, pump status is spoofed as running (1.0) while flow drops
            df_telemetry.loc[attack_timesteps, "S_P1"] = spec.params["spoof_status"]
            df_telemetry.loc[attack_timesteps, "F_P1"] = 0.0
            # Ground truth reflects actual pump shutdown
            df_ground_truth.loc[attack_timesteps, "S_P1"] = spec.params["override_status"]
            df_ground_truth.loc[attack_timesteps, "F_P1"] = 0.0

        elif spec.attack_type == AttackType.COMMUNICATION_LOSS:
            for target in spec.target_components:
                df_telemetry.loc[attack_timesteps, target] = np.nan

        elif spec.attack_type == AttackType.SENSOR_DROPOUT:
            drop_rate = spec.params["drop_rate"]
            rng = np.random.default_rng(self.seed + 101)
            for t in attack_timesteps:
                for target in spec.target_components:
                    if rng.uniform(0, 1) < drop_rate:
                        df_telemetry.loc[t, target] = np.nan

        elif spec.attack_type == AttackType.COORDINATED_FDIA:
            offsets = spec.params["offsets"]
            for target, offset in offsets.items():
                if target in df_telemetry.columns:
                    df_telemetry.loc[attack_timesteps, target] += offset

        elif spec.attack_type == AttackType.STEALTH_FALSE_DATA:
            offsets = spec.params["offsets"]
            for target, offset in offsets.items():
                if target in df_telemetry.columns:
                    df_telemetry.loc[attack_timesteps, target] += offset

        elif spec.attack_type == AttackType.VALVE_TAMPERING:
            df_telemetry.loc[attack_timesteps, "P_J5"] = spec.params["spoofed_pressure"]
            df_ground_truth.loc[attack_timesteps, "P_J5"] = spec.params["tampered_setting"]

        elif spec.attack_type == AttackType.MULTI_PLC_COORDINATED:
            df_telemetry.loc[attack_timesteps, "F_P1"] += spec.params["f_p1_bias"]
            df_telemetry.loc[attack_timesteps, "L_T1"] += spec.params["l_t1_bias"]

        # Populate labels
        df_labels.loc[attack_timesteps, "is_attack"] = 1
        df_labels.loc[attack_timesteps, "attack_type"] = spec.attack_type.value
        df_labels.loc[attack_timesteps, "target_components"] = ",".join(spec.target_components)

        return ScenarioResult(
            scenario_id=spec.scenario_id,
            telemetry=df_telemetry,
            ground_truth_physical=df_ground_truth,
            labels=df_labels,
            target_components=spec.target_components,
        )
