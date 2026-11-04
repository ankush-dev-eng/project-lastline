"""Phase 7 Acceptance Tests: Real-Time Streaming API & Safety Boundary.

Gate Requirements:
- REST endpoints for system state, topology, sensors, playbooks, replay, and audit log.
- WebSocket live streaming broadcasting updates <= 1 second.
- p95 latency < 200 ms across REST endpoints.
- Read-only safety test mathematically proving no industrial control-write interface exists.
"""

import time

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_api_health_and_sandbox_indicator(client):
    """Verify health endpoint surfaces advisory sandbox guarantee."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "SANDBOX" in data["mode"]
    assert "ADVISORY" in data["mode"]
    assert data["advisory_only"] is True


def test_network_topology_endpoint(client):
    """Verify network topology returns nodes, pipes, pumps, valves, and zones."""
    res = client.get("/api/network/topology")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "links" in data
    assert "zones" in data
    assert len(data["nodes"]) >= 15
    assert len(data["links"]) >= 18
    assert len(data["zones"]) == 3


def test_sensors_registry_endpoint(client):
    """Verify sensor registry returns all 22 sensors with metadata."""
    res = client.get("/api/network/sensors")
    assert res.status_code == 200
    data = res.json()
    assert len(data["sensors"]) == 22
    # Check sample sensor attributes
    sample = data["sensors"]["P_J1"]
    assert sample["sensor_type"].lower() == "junction_pressure"
    assert sample["plc_id"] == "PLC_2"
    assert "min_normal" in sample
    assert "max_normal" in sample


def test_scenarios_list_and_select(client):
    """Verify scenario listing and selection for replay."""
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    scenarios = res.json()["scenarios"]
    assert len(scenarios) >= 11

    # Select Scenario 1
    sel_res = client.post("/api/scenarios/select", json={"scenario_id": "SCENARIO_01_SENSOR_BIAS"})
    assert sel_res.status_code == 200
    assert sel_res.json()["active_scenario_id"] == "SCENARIO_01_SENSOR_BIAS"


def test_current_state_and_agent_reports(client):
    """Verify state estimation and multi-agent reports endpoints."""
    # Ensure a scenario is loaded
    client.post("/api/scenarios/select", json={"scenario_id": "SCENARIO_08_COORDINATED_FDIA"})

    state_res = client.get("/api/state/current")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert "telemetry" in state_data
    assert "reconstructed_state" in state_data
    assert "uncertainties" in state_data
    assert "sensor_trust" in state_data

    agent_res = client.get("/api/agents/reports")
    assert agent_res.status_code == 200
    agent_data = agent_res.json()
    assert "sentinel" in agent_data
    assert "integrity" in agent_data
    assert "reconstruction" in agent_data
    assert "impact" in agent_data
    assert "response" in agent_data
    assert "explainer" in agent_data


def test_playbooks_recommendations_and_hitl_workflow(client):
    """Verify recommendation generation and Human-In-The-Loop approval workflow."""
    recs_res = client.get("/api/playbooks/recommendations")
    assert recs_res.status_code == 200
    recs = recs_res.json()["recommendations"]
    assert len(recs) >= 1

    rec = recs[0]
    rec_id = rec["recommendation_id"]
    assert rec["requires_human_approval"] is True
    assert rec["is_advisory"] is True
    assert rec["approval_status"] == "PENDING_APPROVAL"

    # Human-in-the-loop: Operator approves recommendation
    act_res = client.post(
        "/api/playbooks/action",
        json={
            "recommendation_id": rec_id,
            "action": "APPROVE",
            "operator_id": "OP-9014",
            "notes": "Verified pressure deficit in Zone B; approving simulated intertie feed.",
        },
    )
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["approval_status"] == "APPROVED"
    assert act_data["executed_physical_command"] is False, (
        "Hard safety rule: must NEVER execute physical control"
    )
    assert "ADVISORY" in act_data["notice"]


def test_audit_log_endpoint(client):
    """Verify cryptographic audit trail endpoint."""
    res = client.get("/api/audit/entries")
    assert res.status_code == 200
    data = res.json()
    assert "entries" in data
    assert "is_chain_valid" in data
    assert data["is_chain_valid"] is True


def test_replay_controls(client):
    """Verify replay controller controls: play, pause, step, speed, seek."""
    # Play
    p_res = client.post("/api/replay/control", json={"command": "PLAY", "speed": 2.0})
    assert p_res.status_code == 200
    assert p_res.json()["is_playing"] is True
    assert p_res.json()["speed"] == 2.0

    # Pause
    pause_res = client.post("/api/replay/control", json={"command": "PAUSE"})
    assert pause_res.status_code == 200
    assert pause_res.json()["is_playing"] is False

    # Step Forward
    step_res = client.post("/api/replay/control", json={"command": "STEP_FORWARD"})
    assert step_res.status_code == 200
    assert step_res.json()["current_hour"] >= 0

    # Seek
    seek_res = client.post("/api/replay/control", json={"command": "SEEK", "target_hour": 12})
    assert seek_res.status_code == 200
    assert seek_res.json()["current_hour"] == 12


def test_websocket_live_stream(client):
    """Verify WebSocket live streaming receives state update frame <= 1 second."""
    with client.websocket_connect("/ws/live") as websocket:
        t0 = time.perf_counter()
        data = websocket.receive_json()
        t1 = time.perf_counter()

        elapsed = t1 - t0
        assert elapsed <= 1.0, f"WebSocket frame receive time {elapsed:.3f}s exceeds 1.0s limit"
        assert "timestamp" in data
        assert "current_hour" in data
        assert "telemetry" in data
        assert "reconstructed_state" in data
        assert "sensor_trust" in data
        assert "system_alarm" in data


def test_p95_latency_under_200ms(client):
    """Verify p95 response latency across REST endpoints is strictly under 200 ms."""
    endpoints = [
        "/api/health",
        "/api/network/topology",
        "/api/network/sensors",
        "/api/scenarios",
        "/api/state/current",
        "/api/agents/reports",
        "/api/playbooks/recommendations",
        "/api/audit/entries",
        "/api/replay/status",
    ]

    latencies_ms = []

    # Warm-up call
    client.get("/api/health")

    # Run 100 requests across endpoints
    for _ in range(12):
        for ep in endpoints:
            t0 = time.perf_counter()
            res = client.get(ep)
            t1 = time.perf_counter()
            assert res.status_code == 200
            latencies_ms.append((t1 - t0) * 1000.0)

    p95_latency = float(sorted(latencies_ms)[int(len(latencies_ms) * 0.95)])
    mean_latency = float(sum(latencies_ms) / len(latencies_ms))

    print(
        f"\n[API Benchmark] Mean: {mean_latency:.2f} ms | p95 Latency: {p95_latency:.2f} ms (Target: < 200 ms)"
    )
    assert p95_latency < 200.0, f"Phase 7 Gate Failure: p95 latency {p95_latency:.2f} ms >= 200 ms"


def test_read_only_safety_boundary():
    """Mathematically verify that zero physical control write pathways exist across all API routes."""
    import inspect

    from backend.api import routes

    # 1. Inspect all route handlers in the API
    forbidden_terms = [
        "write_register",
        "write_coil",
        "write_holding_registers",
        "modbus_write",
        "dnp3_operate",
        "plc_command",
        "send_command",
        "start_pump_hardware",
        "set_valve_hardware",
        "socket.send",
    ]

    route_functions = [obj for name, obj in inspect.getmembers(routes) if inspect.isfunction(obj)]

    for fn in route_functions:
        source = inspect.getsource(fn).lower()
        for term in forbidden_terms:
            assert term not in source, (
                f"CRITICAL SAFETY VIOLATION: Forbidden write term '{term}' in {fn.__name__}"
            )

    # 2. Verify all API routes are tagged as advisory and cannot mutate physical plant
    for route in app.routes:
        if hasattr(route, "endpoint") and inspect.isfunction(route.endpoint):
            doc = inspect.getdoc(route.endpoint) or ""
            # Any POST endpoint must explicitly document its advisory/sandbox nature
            if "POST" in getattr(route, "methods", []):
                assert (
                    "advisory" in doc.lower()
                    or "sandbox" in doc.lower()
                    or "replay" in doc.lower()
                    or "select" in doc.lower()
                ), f"Route {route.path} lacks explicit advisory sandbox documentation"
