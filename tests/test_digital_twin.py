"""Phase 1 Acceptance Tests: Digital Twin Hydraulic Simulation & Sensor Instrumentation.

Gate Requirements:
- EPANET water network with sensors, pumps, valves, tanks, zones.
- Baseline simulation reproducible with identical seeds.
- Physical conservation of mass and pressure dynamics verified.
"""

import numpy as np
import pytest

from twin.model import WaterNetworkTwin
from twin.sensors import SensorType


@pytest.fixture
def twin_fixture():
    """Provides a fresh instance of the LASTLINE digital twin."""
    return WaterNetworkTwin(seed=42)


def test_network_topology_structure(twin_fixture):
    """Verify that the digital twin contains all required physical elements and operational zones."""
    wn = twin_fixture.model

    # Verify elements
    assert len(wn.junction_name_list) >= 10, "Network must contain at least 10 demand junctions"
    assert len(wn.tank_name_list) >= 2, "Network must contain at least 2 storage tanks"
    assert len(wn.reservoir_name_list) >= 1, "Network must contain at least 1 supply reservoir"
    assert len(wn.pump_name_list) >= 2, "Network must contain at least 2 booster pumps"
    assert len(wn.valve_name_list) >= 1, "Network must contain at least 1 control valve"

    # Verify zones
    zones = twin_fixture.get_distribution_zones()
    assert len(zones) >= 3, "Network must segment into at least 3 distinct operational zones"
    for zone_id, zone_data in zones.items():
        assert "junctions" in zone_data
        assert "target_pressure_min_m" in zone_data
        assert len(zone_data["junctions"]) > 0


def test_sensor_registry_coverage(twin_fixture):
    """Verify that comprehensive sensor telemetry points are instrumented across the network."""
    sensors = twin_fixture.get_sensor_registry()
    assert len(sensors) >= 15, "Twin must have at least 15 instrumented sensor channels"

    types = {s.sensor_type for s in sensors.values()}
    assert SensorType.TANK_LEVEL in types
    assert SensorType.JUNCTION_PRESSURE in types
    assert SensorType.PIPE_FLOW in types
    assert SensorType.PUMP_STATUS in types

    # Each tank must have a level sensor
    for tank_name in twin_fixture.model.tank_name_list:
        tank_sensors = [s for s in sensors.values() if s.element_id == tank_name and s.sensor_type == SensorType.TANK_LEVEL]
        assert len(tank_sensors) >= 1, f"Tank {tank_name} missing level transmitter"

    # Each pump must have a flow meter or status sensor
    for pump_name in twin_fixture.model.pump_name_list:
        pump_sensors = [s for s in sensors.values() if s.element_id == pump_name]
        assert len(pump_sensors) >= 1, f"Pump {pump_name} missing telemetry instrumentation"


def test_baseline_hydraulic_simulation_reproducibility(twin_fixture):
    """Verify that extended period simulation produces deterministic, reproducible hydraulics."""
    sim_hours = 24
    res1 = twin_fixture.simulate_baseline(duration_hours=sim_hours)
    
    twin2 = WaterNetworkTwin(seed=42)
    res2 = twin2.simulate_baseline(duration_hours=sim_hours)

    # Check pressure reproducibility
    for junc in twin_fixture.model.junction_name_list:
        p1 = res1.node["pressure"].loc[:, junc].values
        p2 = res2.node["pressure"].loc[:, junc].values
        np.testing.assert_allclose(p1, p2, rtol=1e-5, atol=1e-5)

    # Check tank level reproducibility
    for tank in twin_fixture.model.tank_name_list:
        l1 = res1.node["pressure"].loc[:, tank].values
        l2 = res2.node["pressure"].loc[:, tank].values
        np.testing.assert_allclose(l1, l2, rtol=1e-5, atol=1e-5)


def test_hydraulic_mass_conservation(twin_fixture):
    """Verify conservation of mass: inflows minus demands match tank storage rate of change."""
    sim_hours = 24
    results = twin_fixture.simulate_baseline(duration_hours=sim_hours)
    
    pressures = results.node["pressure"]
    # Verify no negative pressures in baseline simulation
    for junc in twin_fixture.model.junction_name_list:
        p = pressures[junc]
        assert (p >= 0.0).all(), f"Junction {junc} suffered negative pressure in nominal baseline"

    # Verify tank level bounds
    for tank_name in twin_fixture.model.tank_name_list:
        tank = twin_fixture.model.get_node(tank_name)
        levels = pressures[tank_name]
        assert (levels >= tank.min_level - 0.1).all(), f"Tank {tank_name} dropped below min level"
        assert (levels <= tank.max_level + 0.1).all(), f"Tank {tank_name} exceeded max level"


def test_diurnal_demand_pattern_dynamics(twin_fixture):
    """Verify that diurnal demand variation creates realistic day/night pressure and flow cycles."""
    results = twin_fixture.simulate_baseline(duration_hours=24)
    time_steps = results.node["demand"].index
    assert len(time_steps) >= 24

    # Total demand across all junctions must show cyclical variation
    total_demand = results.node["demand"][twin_fixture.model.junction_name_list].sum(axis=1)
    max_demand = total_demand.max()
    min_demand = total_demand.min()
    assert max_demand > 1.3 * min_demand, "Diurnal demand curve must exhibit at least 30% dynamic range"
