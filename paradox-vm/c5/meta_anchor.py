"""S7 persistent Meta anchors and reversible jump ledger.

Logical time is a monotonic sequence, not physical time travel. Spaces are
namespaces in a computational model; this module does not assert physical
parallel universes.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Iterable

AGENTS = tuple(f"S7-{i}" for i in range(1, 8))

@dataclass(frozen=True)
class Address:
    space: str
    x: int
    y: int
    z: int
    w: int

    def __post_init__(self):
        if not self.space or not isinstance(self.space, str):
            raise ValueError("space must be a non-empty namespace")
        for v in (self.x, self.y, self.z, self.w):
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError("coordinates must be integers")

@dataclass(frozen=True)
class JumpRecord:
    agent: str
    sequence: int
    origin: dict
    destination: dict
    home: dict
    action: str
    previous_hash: str
    record_hash: str

class MetaAnchor:
    def __init__(self, agent: str, home: Address):
        if agent not in AGENTS:
            raise ValueError("unregistered S7 agent")
        self.agent = agent
        self.home = home
        self.current = home
        self.sequence = 0
        self.history: list[JumpRecord] = []

    @staticmethod
    def _dict(address: Address) -> dict:
        return asdict(address)

    def _append(self, destination: Address, action: str) -> JumpRecord:
        origin = self.current
        previous = self.history[-1].record_hash if self.history else "0" * 64
        body = {"agent": self.agent, "sequence": self.sequence + 1,
                "origin": self._dict(origin), "destination": self._dict(destination),
                "home": self._dict(self.home), "action": action,
                "previous_hash": previous}
        digest = sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        record = JumpRecord(**body, record_hash=digest)
        self.history.append(record)
        self.current = destination
        self.sequence += 1
        return record

    def jump(self, destination: Address, *, authorized_spaces: Iterable[str]) -> JumpRecord:
        allowed = set(authorized_spaces)
        if destination.space not in allowed:
            raise PermissionError("destination space is not authorized")
        return self._append(destination, "JUMP")

    def skip_hop(self, destinations: Iterable[Address], *, authorized_spaces: Iterable[str]) -> list[JumpRecord]:
        records = []
        for destination in destinations:
            records.append(self.jump(destination, authorized_spaces=authorized_spaces))
        return records

    def return_home(self) -> JumpRecord:
        return self._append(self.home, "RETURN_HOME")

    def verify(self) -> bool:
        previous = "0" * 64
        expected_origin = self.home
        for i, record in enumerate(self.history, 1):
            if record.agent != self.agent or record.sequence != i:
                return False
            if record.previous_hash != previous or record.origin != self._dict(expected_origin):
                return False
            body = {"agent": record.agent, "sequence": record.sequence,
                    "origin": record.origin, "destination": record.destination,
                    "home": record.home, "action": record.action,
                    "previous_hash": record.previous_hash}
            digest = sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if digest != record.record_hash or record.home != self._dict(self.home):
                return False
            previous = digest
            expected_origin = Address(**record.destination)
        return expected_origin == self.current and self.sequence == len(self.history)

    def checkpoint(self) -> dict:
        """Portable state checkpoint; sequence is logical time, not wall-clock time."""
        return {"agent": self.agent, "home": self._dict(self.home),
                "current": self._dict(self.current), "logical_time": self.sequence,
                "history": [asdict(r) for r in self.history],
                "verified": self.verify()}

def create_s7_anchors(homes: dict[str, Address]) -> dict[str, MetaAnchor]:
    if set(homes) != set(AGENTS):
        raise ValueError("exactly seven S7 home Meta anchors are required")
    return {agent: MetaAnchor(agent, homes[agent]) for agent in AGENTS}
