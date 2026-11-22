"""S7 durable Meta anchors with atomic hops and restart recovery.

Logical time is a monotonic event sequence, not physical time travel. Space
namespaces are computational identifiers, not claims about physical universes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable

AGENTS = tuple(f"S7-{i}" for i in range(1, 8))
SCHEMA = "paradox-s7-checkpoint-v2"
GENESIS = "0" * 64


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(value: dict) -> str:
    return sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True)
class Address:
    space: str
    x: int
    y: int
    z: int
    w: int

    def __post_init__(self):
        if not isinstance(self.space, str) or not self.space.strip():
            raise ValueError("space must be a non-empty namespace")
        for value in (self.x, self.y, self.z, self.w):
            if type(value) is not int:
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
        if not isinstance(home, Address):
            raise TypeError("home must be an Address")
        self.agent = agent
        self.home = home
        self.current = home
        self.sequence = 0
        self.history: list[JumpRecord] = []

    @staticmethod
    def _dict(address: Address) -> dict:
        return asdict(address)

    def _make_record(self, origin: Address, destination: Address,
                     sequence: int, action: str, previous: str) -> JumpRecord:
        body = {
            "agent": self.agent,
            "sequence": sequence,
            "origin": self._dict(origin),
            "destination": self._dict(destination),
            "home": self._dict(self.home),
            "action": action,
            "previous_hash": previous,
        }
        return JumpRecord(**body, record_hash=_digest(body))

    def _append(self, destination: Address, action: str) -> JumpRecord:
        if not isinstance(destination, Address):
            raise TypeError("destination must be an Address")
        previous = self.history[-1].record_hash if self.history else GENESIS
        record = self._make_record(self.current, destination, self.sequence + 1,
                                   action, previous)
        self.history.append(record)
        self.current = destination
        self.sequence += 1
        return record

    def jump(self, destination: Address, *, authorized_spaces: Iterable[str]) -> JumpRecord:
        if not isinstance(destination, Address):
            raise TypeError("destination must be an Address")
        allowed = set(authorized_spaces)
        if destination.space not in allowed:
            raise PermissionError("destination space is not authorized")
        return self._append(destination, "JUMP")

    def skip_hop(self, destinations: Iterable[Address], *,
                 authorized_spaces: Iterable[str]) -> list[JumpRecord]:
        """Commit all hops or none; validation happens before state mutation."""
        hops = list(destinations)
        allowed = set(authorized_spaces)
        if any(not isinstance(item, Address) for item in hops):
            raise TypeError("every hop must be an Address")
        denied = [item.space for item in hops if item.space not in allowed]
        if denied:
            raise PermissionError("one or more skip-hop destinations are not authorized")

        original_current, original_sequence = self.current, self.sequence
        original_history_len = len(self.history)
        created = []
        try:
            for destination in hops:
                created.append(self._append(destination, "SKIP_HOP"))
        except Exception:
            del self.history[original_history_len:]
            self.current, self.sequence = original_current, original_sequence
            raise
        return created

    def return_home(self) -> JumpRecord:
        return self._append(self.home, "RETURN_HOME")

    def verify(self) -> bool:
        previous = GENESIS
        expected_origin = self.home
        for index, record in enumerate(self.history, 1):
            if not isinstance(record, JumpRecord):
                return False
            if record.agent != self.agent or record.sequence != index:
                return False
            if record.previous_hash != previous:
                return False
            if record.origin != self._dict(expected_origin):
                return False
            if record.home != self._dict(self.home):
                return False
            if record.action not in {"JUMP", "SKIP_HOP", "RETURN_HOME"}:
                return False
            try:
                destination = Address(**record.destination)
            except (TypeError, ValueError):
                return False
            body = {
                "agent": record.agent, "sequence": record.sequence,
                "origin": record.origin, "destination": record.destination,
                "home": record.home, "action": record.action,
                "previous_hash": record.previous_hash,
            }
            digest = _digest(body)
            if digest != record.record_hash:
                return False
            previous = digest
            expected_origin = destination
        return (expected_origin == self.current and
                self.sequence == len(self.history))

    def checkpoint(self) -> dict:
        """Return a self-checking portable snapshot (not an identity signature)."""
        if not self.verify():
            raise ValueError("cannot checkpoint an invalid S7 history")
        body = {
            "schema": SCHEMA,
            "agent": self.agent,
            "home": self._dict(self.home),
            "current": self._dict(self.current),
            "logical_time": self.sequence,
            "history": [asdict(record) for record in self.history],
        }
        return {**body, "checkpoint_hash": _digest(body)}

    def save(self, path: str | os.PathLike) -> str:
        """Durably replace one checkpoint file using same-directory atomic rename."""
        checkpoint = self.checkpoint()
        payload = _canonical(checkpoint) + b"\n"
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp",
                                         dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            # Best-effort directory sync makes the rename durable on POSIX.
            if hasattr(os, "O_DIRECTORY"):
                dir_fd = os.open(str(target.parent), os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
        return sha256(payload).hexdigest()

    @classmethod
    def from_checkpoint(cls, checkpoint: dict) -> "MetaAnchor":
        if not isinstance(checkpoint, dict):
            raise ValueError("checkpoint must be an object")
        required = {"schema", "agent", "home", "current", "logical_time",
                    "history", "checkpoint_hash"}
        if set(checkpoint) != required or checkpoint.get("schema") != SCHEMA:
            raise ValueError("unsupported or malformed checkpoint schema")
        body = {key: checkpoint[key] for key in required if key != "checkpoint_hash"}
        if _digest(body) != checkpoint["checkpoint_hash"]:
            raise ValueError("checkpoint digest mismatch")
        agent = checkpoint["agent"]
        if agent not in AGENTS:
            raise ValueError("unregistered S7 agent")
        try:
            home = Address(**checkpoint["home"])
            current = Address(**checkpoint["current"])
            raw_history = checkpoint["history"]
            logical_time = checkpoint["logical_time"]
            if not isinstance(raw_history, list) or type(logical_time) is not int:
                raise ValueError("invalid checkpoint history or logical time")
            anchor = cls(agent, home)
            records = []
            for item in raw_history:
                if not isinstance(item, dict) or set(item) != {
                    "agent", "sequence", "origin", "destination", "home",
                    "action", "previous_hash", "record_hash"
                }:
                    raise ValueError("malformed jump record")
                records.append(JumpRecord(**item))
            anchor.history = records
            anchor.current = current
            anchor.sequence = logical_time
        except (TypeError, KeyError) as exc:
            raise ValueError("malformed checkpoint contents") from exc
        if not anchor.verify():
            raise ValueError("checkpoint history verification failed")
        return anchor

    @classmethod
    def restore(cls, path: str | os.PathLike) -> "MetaAnchor":
        """Load and independently verify a checkpoint from durable storage."""
        try:
            with open(path, "rb") as stream:
                raw = stream.read()
            checkpoint = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("checkpoint could not be read") from exc
        return cls.from_checkpoint(checkpoint)


def create_s7_anchors(homes: dict[str, Address]) -> dict[str, MetaAnchor]:
    if set(homes) != set(AGENTS):
        raise ValueError("exactly seven S7 home Meta anchors are required")
    return {agent: MetaAnchor(agent, homes[agent]) for agent in AGENTS}
