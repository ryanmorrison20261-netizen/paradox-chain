"""Infinite 7x7x7 Paradox lattice with lazy hierarchical addressing.

The model is an executable mathematical rule system, not a claim about
physical parallel universes. It stores no infinite collection: coordinates
and child paths are generated on demand.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

WIDTH = 7
CELLS_PER_BLOCK = WIDTH ** 3
WAYS_PER_LAYER = WIDTH ** 2
LAYERS_PER_BLOCK = WIDTH


@dataclass(frozen=True, order=True)
class Cell:
    """A cell address within one 7x7x7 block; coordinates are 0..6."""
    x: int
    y: int
    z: int

    def __post_init__(self) -> None:
        if any(type(v) is not int or not 0 <= v < WIDTH for v in (self.x, self.y, self.z)):
            raise ValueError("cell coordinates must be integers in range 0..6")


@dataclass(frozen=True)
class HierarchicalAddress:
    """A path of child-cell choices; empty path identifies the root."""
    path: tuple[Cell, ...] = ()

    def child(self, cell: Cell) -> "HierarchicalAddress":
        if not isinstance(cell, Cell):
            raise TypeError("child address requires a Cell")
        return HierarchicalAddress(self.path + (cell,))

    @property
    def depth(self) -> int:
        return len(self.path)

    def parent(self) -> "HierarchicalAddress":
        if not self.path:
            raise ValueError("root address has no parent")
        return HierarchicalAddress(self.path[:-1])

    def encode(self) -> str:
        if not self.path:
            return "P"
        return "P/" + "/".join(f"{c.x}{c.y}{c.z}" for c in self.path)


def cells() -> Iterable[Cell]:
    """Yield all 343 cells exactly once in stable z/y/x order."""
    for z, y, x in product(range(WIDTH), repeat=3):
        yield Cell(x, y, z)


def layer_cells(z: int) -> tuple[Cell, ...]:
    """Return one 7x7 layer: exactly 49 distinct ways."""
    if type(z) is not int or not 0 <= z < WIDTH:
        raise ValueError("layer index must be an integer in range 0..6")
    return tuple(Cell(x, y, z) for y in range(WIDTH) for x in range(WIDTH))


def neighbours(coord: tuple[int, int, int]) -> dict[str, tuple[int, int, int]]:
    """Six face-adjacent neighbours in the unbounded integer lattice."""
    if (not isinstance(coord, tuple) or len(coord) != 3
            or any(type(v) is not int for v in coord)):
        raise ValueError("coord must be a tuple of three integers")
    x, y, z = coord
    return {
        "x-": (x - 1, y, z), "x+": (x + 1, y, z),
        "y-": (x, y - 1, z), "y+": (x, y + 1, z),
        "z-": (x, y, z - 1), "z+": (x, y, z + 1),
    }


def expand(address: HierarchicalAddress, depth: int) -> tuple[HierarchicalAddress, ...]:
    """Generate one finite frontier lazily by requested depth.

    A depth-d frontier has 343**d addresses; callers should request modest
    depths or stream cells() and child() rather than materialize huge frontiers.
    """
    if type(depth) is not int or depth < 0:
        raise ValueError("depth must be a non-negative integer")
    frontier = (address,)
    for _ in range(depth):
        frontier = tuple(parent.child(cell) for parent in frontier for cell in cells())
    return frontier
