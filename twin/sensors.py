"""PROJECT LASTLINE: Sensor Instrumentation & Telemetry Metadata.

Defines sensor types, measurement units, and PLC mapping for operational technology monitoring.
"""

from enum import Enum
from pydantic import BaseModel, Field


class SensorType(str, Enum):
    TANK_LEVEL = "tank_level"
    JUNCTION_PRESSURE = "junction_pressure"
    PIPE_FLOW = "pipe_flow"
    PUMP_STATUS = "pump_status"
    PUMP_SPEED = "pump_speed"
    VALVE_STATUS = "valve_status"


class SensorMetadata(BaseModel):
    """Metadata for an instrumented physical sensor deployed in the water network."""
    sensor_id: str
    sensor_type: SensorType
    element_id: str
    plc_id: str
    unit: str
    min_normal: float
    max_normal: float
    noise_std: float = 0.01  # Gaussian measurement noise std relative to scale
    criticality: str = Field(default="medium", description="criticality rating: low, medium, high, critical")
    zone_id: str | None = None
