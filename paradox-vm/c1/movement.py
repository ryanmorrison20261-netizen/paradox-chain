"""Deterministic one-dimensional movement engine using Decimal SI units.

This is a kinematic position-state simulator, not a physics engine or a
connection to a running virtual machine. Distances are metres by default.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from typing import Optional


def _decimal(value: object) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("distance must be a finite decimal number") from exc
    if not result.is_finite():
        raise ValueError("distance must be finite")
    return result


@dataclass(frozen=True)
class Movement:
    sequence: int
    direction: str
    distance_m: str
    start_m: str
    end_m: str


class C1Movement:
    """A bounded or unbounded 1-D position model, measured in metres."""

    def __init__(self, start_m: object = 0, min_m: Optional[object] = None,
                 max_m: Optional[object] = None):
        self.position = _decimal(start_m)
        self.min_m = _decimal(min_m) if min_m is not None else None
        self.max_m = _decimal(max_m) if max_m is not None else None
        if self.min_m is not None and self.max_m is not None and self.min_m > self.max_m:
            raise ValueError("min_m cannot exceed max_m")
        self._check_bounds(self.position)
        self.history: list[Movement] = []

    def _check_bounds(self, position: Decimal) -> None:
        if self.min_m is not None and position < self.min_m:
            raise ValueError("movement would cross minimum boundary")
        if self.max_m is not None and position > self.max_m:
            raise ValueError("movement would cross maximum boundary")

    def move(self, direction: str, distance_m: object) -> Movement:
        if direction not in ("forward", "backward"):
            raise ValueError("direction must be 'forward' or 'backward'")
        distance = _decimal(distance_m)
        if distance < 0:
            raise ValueError("distance must be non-negative; choose direction separately")
        start = self.position
        end = start + distance if direction == "forward" else start - distance
        self._check_bounds(end)  # Validate before mutating state.
        event = Movement(
            sequence=len(self.history) + 1,
            direction=direction,
            distance_m=str(distance),
            start_m=str(start),
            end_m=str(end),
        )
        self.position = end
        self.history.append(event)
        return event

    def snapshot(self) -> dict:
        return {
            "unit": "metre",
            "position_m": str(self.position),
            "movement_count": len(self.history),
            "history": [asdict(event) for event in self.history],
        }


def run_c1_test() -> dict:
    vm = C1Movement(start_m="0")
    vm.move("backward", "5")
    vm.move("forward", "50")
    result = vm.snapshot()
    result["expected_position_m"] = "45"
    result["passed"] = vm.position == Decimal("45")
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(run_c1_test(), indent=2))
