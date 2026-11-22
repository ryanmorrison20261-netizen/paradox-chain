"""Infinite 343 / 3x3 Paradox lattice address model.

The model is mathematically unbounded (integer block coordinates) but lazy:
it stores only addresses requested by a caller. Every block has a 3x3
top-level cell map; each cell can be expanded into a 7x7x7 (343) child
address space, recursively, without materializing the infinite structure.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

RADIX = 7
BLOCK_SIZE = RADIX ** 3  # 343
GRID_SIDE = 3
GRID_CELLS = GRID_SIDE ** 2  # 9
DIRECTIONS = {
    "xp": (1, 0, 0), "xn": (-1, 0, 0),
    "yp": (0, 1, 0), "yn": (0, -1, 0),
    "zp": (0, 0, 1), "zn": (0, 0, -1),
}

def _int3(values):
    result=tuple(values)
    if len(result)!=3 or any(type(v) is not int for v in result):
        raise ValueError("block coordinate must contain three integers")
    return result

def encode_child(x, y, z):
    """Encode integer local coordinates 0..6 as a stable index 0..342."""
    if any(type(v) is not int or not 0 <= v < RADIX for v in (x,y,z)):
        raise ValueError("child coordinates must each be integers from 0 through 6")
    return x + RADIX*y + RADIX*RADIX*z

def decode_child(index):
    if type(index) is not int or not 0 <= index < BLOCK_SIZE:
        raise ValueError("child index must be an integer from 0 through 342")
    z, rem = divmod(index, RADIX*RADIX)
    y, x = divmod(rem, RADIX)
    return (x,y,z)

def cell3x3(row, col):
    if type(row) is not int or type(col) is not int or not (0 <= row < 3 and 0 <= col < 3):
        raise ValueError("3x3 cell coordinates must be integers from 0 through 2")
    return row*GRID_SIDE+col

def decode_cell(index):
    if type(index) is not int or not 0 <= index < GRID_CELLS:
        raise ValueError("cell index must be an integer from 0 through 8")
    return divmod(index, GRID_SIDE)

@dataclass(frozen=True, order=True)
class BlockAddress:
    x: int
    y: int
    z: int
    def __post_init__(self):
        _int3((self.x,self.y,self.z))
    @property
    def tuple(self): return (self.x,self.y,self.z)
    def neighbour(self, direction):
        if direction not in DIRECTIONS: raise ValueError("unknown direction")
        d=DIRECTIONS[direction]
        return BlockAddress(self.x+d[0],self.y+d[1],self.z+d[2])
    def to_dict(self): return {"block":[self.x,self.y,self.z]}

@dataclass(frozen=True, order=True)
class NodeAddress:
    block: BlockAddress
    cell: int
    path: tuple[int,...] = ()
    def __post_init__(self):
        if not 0 <= self.cell < GRID_CELLS: raise ValueError("cell must be 0..8")
        if any(type(i) is not int or not 0 <= i < BLOCK_SIZE for i in self.path):
            raise ValueError("each nested child index must be 0..342")
    def child(self, x, y, z):
        return NodeAddress(self.block,self.cell,self.path+(encode_child(x,y,z),))
    def parent(self):
        if not self.path: return None
        return NodeAddress(self.block,self.cell,self.path[:-1])
    @property
    def depth(self): return len(self.path)
    def to_dict(self):
        return {"block":[self.block.x,self.block.y,self.block.z],
                "cell":self.cell,"path":list(self.path),"depth":self.depth}
    @property
    def stable_id(self):
        raw=json.dumps(self.to_dict(),sort_keys=True,separators=(",",":")).encode()
        return sha256(b"PARADOX-INFINITE343-v1\0"+raw).hexdigest()

class Infinite343:
    """Lazy infinite block lattice with nine cells and recursive 343 branching."""
    schema="paradox-infinite343-v1"
    def address(self, block=(0,0,0), cell=0, path=()):
        return NodeAddress(BlockAddress(*_int3(block)),cell,tuple(path))
    def block_neighbour(self, block, direction):
        return BlockAddress(*_int3(block)).neighbour(direction)
    def expand(self, node):
        if not isinstance(node,NodeAddress): raise TypeError("node must be NodeAddress")
        # Yield, do not store, exactly 343 direct children.
        for z in range(7):
            for y in range(7):
                for x in range(7):
                    yield node.child(x,y,z)
    def cell_grid(self, block=(0,0,0)):
        b=BlockAddress(*_int3(block))
        return tuple(NodeAddress(b,cell,()) for cell in range(GRID_CELLS))
    def neighbourhood(self, block=(0,0,0)):
        b=BlockAddress(*_int3(block))
        return {name:b.neighbour(name) for name in DIRECTIONS}
    def manifest(self, node):
        if not isinstance(node,NodeAddress): raise TypeError("node must be NodeAddress")
        return {"schema":self.schema,"block":[node.block.x,node.block.y,node.block.z],
                "grid_shape":[3,3],"grid_cells":9,"branching_shape":[7,7,7],
                "children_per_node":343,"depth":node.depth,
                "node_id":node.stable_id,"materialized_children":0,
                "expansion":"lazy"}
