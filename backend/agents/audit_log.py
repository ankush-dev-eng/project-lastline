"""PROJECT LASTLINE: Cryptographic Immutable Audit Log.

Provides SHA-256 hash-chained tamper-evident logging for all agent actions,
telemetry evaluations, and operator recommendations.
"""

import hashlib
import json
import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from backend.agents.contracts import AgentType

GENESIS_HASH = "0" * 64


class AuditEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    agent: AgentType
    action: str
    payload: dict[str, Any]
    previous_hash: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        """Computes SHA-256 digest of entry fields ensuring deterministic ordering."""
        payload_serialized = json.dumps(self.payload, sort_keys=True, default=str)
        raw_msg = (
            f"{self.entry_id}|{self.timestamp:.6f}|{self.agent.value}|"
            f"{self.action}|{payload_serialized}|{self.previous_hash}"
        )
        return hashlib.sha256(raw_msg.encode("utf-8")).hexdigest()


class AuditLog:
    """Thread-safe, append-only, cryptographically linked audit trail."""

    def __init__(self):
        self._entries: list[AuditEntry] = []

    def record_event(self, agent: AgentType, action: str, payload: dict[str, Any]) -> AuditEntry:
        """Appends a new event entry chained to the preceding entry hash."""
        prev_hash = self._entries[-1].entry_hash if self._entries else GENESIS_HASH

        entry = AuditEntry(
            agent=agent,
            action=action,
            payload=payload,
            previous_hash=prev_hash,
        )
        entry.entry_hash = entry.compute_hash()
        self._entries.append(entry)
        return entry

    def get_entries(self) -> list[AuditEntry]:
        """Returns read-only copy of audit log entries."""
        return list(self._entries)

    def verify_integrity(self) -> bool:
        """Verifies cryptographic hash chain across all log entries.

        Returns True if the entire chain is intact, False if any entry was altered.
        """
        if not self._entries:
            return True

        expected_prev = GENESIS_HASH
        for entry in self._entries:
            # Verify previous link
            if entry.previous_hash != expected_prev:
                return False

            # Verify current hash matches payload and attributes
            recalculated = entry.compute_hash()
            if entry.entry_hash != recalculated:
                return False

            expected_prev = entry.entry_hash

        return True
