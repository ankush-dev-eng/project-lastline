"""PROJECT LASTLINE: Sentinel Cyber Telemetry Agent.

Monitors industrial network traffic, PLC write requests, protocol violations,
and indicators of compromise (IoC) across OT network segments.
"""

import time
from typing import Any

from backend.agents.contracts import CyberAlert, SentinelReport, SeverityLevel


class SentinelAgent:
    """Specialized agent auditing industrial control network communications."""

    def __init__(self, authorized_subnets: list[str] | None = None):
        self.authorized_subnets = authorized_subnets or ["10.0.1.", "192.168.10."]

    def analyze(self, cyber_events: list[dict[str, Any]] | None = None) -> SentinelReport:
        """Analyzes incoming network/cyber events for indicators of compromise."""
        if not cyber_events:
            return SentinelReport(
                cyber_threat_level=SeverityLevel.LOW,
                flagged_plcs=[],
                alerts=[],
                timestamp=time.time(),
            )

        alerts: list[CyberAlert] = []
        flagged_plcs = set()
        highest_severity = SeverityLevel.LOW

        for idx, ev in enumerate(cyber_events):
            plc_id = ev.get("destination_plc") or ev.get("plc_id", "UNKNOWN_PLC")
            src_ip = ev.get("source_ip", "")
            modbus_fn = ev.get("modbus_function")
            register = ev.get("register", "")
            is_authorized = ev.get("authorized", True)

            # Check unauthorized write or unknown subnet
            is_foreign_ip = not any(src_ip.startswith(prefix) for prefix in self.authorized_subnets)
            is_write_cmd = modbus_fn in (5, 6, 15, 16) or "WRITE" in str(register).upper()

            if not is_authorized or (is_foreign_ip and is_write_cmd):
                severity = SeverityLevel.CRITICAL if is_write_cmd else SeverityLevel.HIGH
                alert = CyberAlert(
                    alert_id=f"CYB-ALT-{idx+1:03d}",
                    plc_id=plc_id,
                    severity=severity,
                    indicator="UNAUTHORIZED_PLC_WRITE_ATTEMPT",
                    details=f"Unauthorized write to register '{register}' on {plc_id} from foreign IP {src_ip}",
                    timestamp=float(ev.get("timestamp", time.time())),
                )
                alerts.append(alert)
                flagged_plcs.add(plc_id)
                highest_severity = SeverityLevel.CRITICAL

            elif is_foreign_ip:
                alert = CyberAlert(
                    alert_id=f"CYB-ALT-{idx+1:03d}",
                    plc_id=plc_id,
                    severity=SeverityLevel.MEDIUM,
                    indicator="UNAUTHORIZED_SUBNET_PROBE",
                    details=f"Inbound connection from untrusted IP {src_ip} targeting {plc_id}",
                    timestamp=float(ev.get("timestamp", time.time())),
                )
                alerts.append(alert)
                flagged_plcs.add(plc_id)
                if highest_severity not in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
                    highest_severity = SeverityLevel.MEDIUM

        return SentinelReport(
            cyber_threat_level=highest_severity,
            flagged_plcs=sorted(list(flagged_plcs)),
            alerts=alerts,
            timestamp=time.time(),
        )
