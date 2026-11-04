"""PROJECT LASTLINE: Simulation Replay Controller.

Manages time-stepping, playback rate, seeking, and pause/play states
for historical incident replay and live scenario streaming.
"""

from pydantic import BaseModel


class ReplayStatus(BaseModel):
    scenario_id: str
    current_hour: int
    max_hours: int
    is_playing: bool
    speed: float


class ReplayController:
    """Controls time-stepped replay of simulated and historical attack telemetry."""

    def __init__(self, scenario_id: str = "SCENARIO_01_SENSOR_BIAS", max_hours: int = 24):
        self.scenario_id = scenario_id
        self.current_hour = 0
        self.max_hours = max_hours
        self.is_playing = False
        self.speed = 1.0

    def play(self, speed: float | None = None) -> ReplayStatus:
        self.is_playing = True
        if speed is not None and speed > 0:
            self.speed = speed
        return self.get_status()

    def pause(self) -> ReplayStatus:
        self.is_playing = False
        return self.get_status()

    def step_forward(self) -> ReplayStatus:
        if self.current_hour < self.max_hours - 1:
            self.current_hour += 1
        return self.get_status()

    def step_backward(self) -> ReplayStatus:
        if self.current_hour > 0:
            self.current_hour -= 1
        return self.get_status()

    def seek(self, hour: int) -> ReplayStatus:
        self.current_hour = max(0, min(hour, self.max_hours - 1))
        return self.get_status()

    def reset(self) -> ReplayStatus:
        self.current_hour = 0
        self.is_playing = False
        return self.get_status()

    def set_scenario(self, scenario_id: str) -> ReplayStatus:
        self.scenario_id = scenario_id
        self.current_hour = 0
        self.is_playing = False
        return self.get_status()

    def get_status(self) -> ReplayStatus:
        return ReplayStatus(
            scenario_id=self.scenario_id,
            current_hour=self.current_hour,
            max_hours=self.max_hours,
            is_playing=self.is_playing,
            speed=self.speed,
        )
