"""PROJECT LASTLINE: FastAPI REST Routes.

Defines all operations endpoints for network topology, live telemetry,
reconstructed state, multi-agent reports, advisory recommendations, and replay controls.

HARD SAFETY GUARANTEE:
All interfaces are strictly read-only and advisory.
No write pathways to physical industrial controllers or hardware actuators exist.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agents.contracts import AgentType
from backend.api.state import get_system_state

router = APIRouter(prefix="/api")


# 1. Health & Sandbox Guarantee
@router.get("/health")
def get_health() -> dict[str, Any]:
    """Surfaces platform operational health and strict advisory sandbox boundary guarantee."""
    return {
        "status": "healthy",
        "version": "0.7.0",
        "mode": "SANDBOX - ADVISORY ONLY",
        "advisory_only": True,
        "physical_control_prohibited": True,
        "system_name": "PROJECT LASTLINE - Cyber-Resilience for Water Infrastructure",
    }


# 2. Network Topology & Sensors
@router.get("/network/topology")
def get_network_topology() -> dict[str, Any]:
    """Returns municipal water distribution network topology, coordinates, and zones."""
    state = get_system_state()
    wn = state.twin.model

    nodes = []
    for name, node in wn.nodes():
        coords = getattr(node, "coordinates", (0.0, 0.0))
        nodes.append(
            {
                "id": name,
                "type": node.node_type,
                "elevation_m": getattr(node, "elevation", 0.0),
                "coordinates": list(coords),
            }
        )

    links = []
    for name, link in wn.links():
        links.append(
            {
                "id": name,
                "type": link.link_type,
                "start_node": link.start_node_name,
                "end_node": link.end_node_name,
                "length_m": getattr(link, "length", 0.0),
                "diameter_m": getattr(link, "diameter", 0.0),
            }
        )

    zones = [
        {
            "zone_id": "Zone_A_North",
            "name": "North Highlands Residential",
            "elevation_range": "25 - 32m",
            "nodes": ["J1", "J2", "J3", "J4", "T1_Highlands"],
            "critical_facilities": ["North Highlands Civic Center"],
        },
        {
            "zone_id": "Zone_B_Central",
            "name": "Central Commercial & Civic",
            "elevation_range": "15 - 20m",
            "nodes": ["J_PRV_Inlet", "J5", "J6", "J7", "J8"],
            "critical_facilities": ["Verdant Memorial Hospital"],
        },
        {
            "zone_id": "Zone_C_Industrial",
            "name": "Eastside Industrial & Tech Center",
            "elevation_range": "10 - 15m",
            "nodes": ["J9", "J10", "J11", "J12", "T2_Eastside"],
            "critical_facilities": ["Eastside High-Tech Industrial Park"],
        },
    ]

    return {
        "network_name": "Verdant City Municipal Water System",
        "nodes": nodes,
        "links": links,
        "zones": zones,
    }


@router.get("/network/sensors")
def get_sensors_registry() -> dict[str, Any]:
    """Returns complete instrument registry with PLC mappings, types, and normal bounds."""
    state = get_system_state()
    sensors = state.twin.get_sensor_registry()
    out = {}
    for sid, s in sensors.items():
        out[sid] = {
            "sensor_id": s.sensor_id,
            "sensor_type": s.sensor_type.value,
            "element_id": s.element_id,
            "plc_id": s.plc_id,
            "unit": s.unit,
            "min_normal": s.min_normal,
            "max_normal": s.max_normal,
            "criticality": s.criticality,
            "zone_id": s.zone_id,
        }
    return {"sensors": out, "total_sensors": len(out)}


# 3. Scenarios & Selection
class ScenarioSelectRequest(BaseModel):
    scenario_id: str


@router.get("/scenarios")
def list_scenarios() -> dict[str, Any]:
    """Lists all registered attack scenarios and benchmark datasets."""
    state = get_system_state()
    scenarios = state.registry.list_scenarios()
    return {
        "scenarios": [
            {
                "scenario_id": s.scenario_id,
                "name": s.name,
                "description": s.description,
                "attack_type": s.attack_type.value,
                "target_components": s.target_components,
                "target_plc": s.target_plc,
                "start_hour": s.start_hour,
                "duration_hours": s.duration_hours,
            }
            for s in scenarios
        ]
    }


@router.post("/scenarios/select")
def select_scenario(req: ScenarioSelectRequest) -> dict[str, Any]:
    """Select active replay scenario for digital twin simulation."""
    state = get_system_state()
    try:
        state.load_scenario(req.scenario_id)
        state.audit_log.record_event(
            agent=AgentType.RESPONSE,
            action="SCENARIO_SELECTED",
            payload={"scenario_id": req.scenario_id},
        )
        return {
            "status": "success",
            "active_scenario_id": req.scenario_id,
            "notice": "SANDBOX SIMULATION LOADED",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 4. Current State & Agent Reports
@router.get("/state/current")
def get_current_state() -> dict[str, Any]:
    """Returns current timestep telemetry, physics reconstruction, uncertainties, and trust scores."""
    state = get_system_state()
    return state.get_current_frame()


@router.get("/agents/reports")
def get_agent_reports() -> dict[str, Any]:
    """Returns comprehensive multi-agent reasoning reports across Sentinel, Integrity, Reconstruction, Impact, Response, and Explainer."""
    state = get_system_state()
    frame = state.get_current_frame()
    return frame["agent_reports"]


# 5. Fallback Recommendations & HITL Approval
class ActionApprovalRequest(BaseModel):
    recommendation_id: str
    action: str = Field(description="APPROVE or REJECT")
    operator_id: str
    notes: str = ""


@router.get("/playbooks/recommendations")
def get_recommendations() -> dict[str, Any]:
    """Returns active pre-approved fallback recommendations verified safe by digital twin simulation."""
    state = get_system_state()
    frame = state.get_current_frame()
    return {
        "recommendations": frame["recommendations"],
        "advisory_mode": True,
        "requires_human_approval": True,
    }


@router.post("/playbooks/action")
def record_operator_action(req: ActionApprovalRequest) -> dict[str, Any]:
    """Advisory Human-in-the-Loop decision: records operator approval or rejection in the audit ledger.

    Guaranteed advisory sandbox operation: executes zero physical hardware or PLC control commands.
    """
    state = get_system_state()
    action_clean = req.action.upper()
    if action_clean not in ("APPROVE", "REJECT"):
        raise HTTPException(status_code=400, detail="Action must be APPROVE or REJECT")

    status_str = "APPROVED" if action_clean == "APPROVE" else "REJECTED"
    state.approval_records[req.recommendation_id] = {
        "status": status_str,
        "operator_id": req.operator_id,
        "notes": req.notes,
    }

    # Record to immutable audit trail
    state.audit_log.record_event(
        agent=AgentType.RESPONSE,
        action=f"OPERATOR_RECOMMENDATION_{status_str}",
        payload={
            "recommendation_id": req.recommendation_id,
            "approval_status": status_str,
            "operator_id": req.operator_id,
            "notes": req.notes,
            "physical_execution": False,
        },
    )

    return {
        "recommendation_id": req.recommendation_id,
        "approval_status": status_str,
        "executed_physical_command": False,
        "notice": "SANDBOX ENVIRONMENT - ADVISORY ONLY - PHYSICAL COMMAND EXECUTION FORBIDDEN",
    }


# 6. Audit Trail
@router.get("/audit/entries")
def get_audit_entries() -> dict[str, Any]:
    """Returns cryptographically linked SHA-256 audit log and chain verification status."""
    state = get_system_state()
    entries = state.audit_log.get_entries()
    is_valid = state.audit_log.verify_integrity()
    return {
        "entries": [e.model_dump() for e in entries],
        "total_entries": len(entries),
        "is_chain_valid": is_valid,
    }


# 7. Replay Controls
class ReplayControlRequest(BaseModel):
    command: str = Field(description="PLAY, PAUSE, STEP_FORWARD, STEP_BACKWARD, SEEK, RESET")
    speed: float | None = None
    target_hour: int | None = None


@router.get("/replay/status")
def get_replay_status() -> dict[str, Any]:
    """Returns current time-step replay controller status."""
    state = get_system_state()
    return state.replay.get_status().model_dump()


@router.post("/replay/control")
def control_replay(req: ReplayControlRequest) -> dict[str, Any]:
    """Replay simulation controller: play, pause, step forward/backward, or seek hours."""
    state = get_system_state()
    cmd = req.command.upper()

    if cmd == "PLAY":
        st = state.replay.play(req.speed)
    elif cmd == "PAUSE":
        st = state.replay.pause()
    elif cmd == "STEP_FORWARD":
        st = state.replay.step_forward()
    elif cmd == "STEP_BACKWARD":
        st = state.replay.step_backward()
    elif cmd == "SEEK":
        if req.target_hour is None:
            raise HTTPException(status_code=400, detail="target_hour required for SEEK")
        st = state.replay.seek(req.target_hour)
    elif cmd == "RESET":
        st = state.replay.reset()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown replay command '{cmd}'")

    return st.model_dump()
