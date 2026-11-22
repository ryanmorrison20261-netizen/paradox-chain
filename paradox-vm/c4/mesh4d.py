"""C4: permissioned 4D and parallel-space mesh topology.

This is a deterministic in-process reference model. It does not open sockets,
authenticate real remote machines, or prove physical parallel universes.
Cross-space bridges require explicit authorization metadata.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

RADIX = 7
BLOCK_4D_SIZE = RADIX ** 4  # 2401
LAYER_3D_SIZE = RADIX ** 3  # 343
DIRECTIONS_4D = {
    "x-": (-1, 0, 0, 0), "x+": (1, 0, 0, 0),
    "y-": (0, -1, 0, 0), "y+": (0, 1, 0, 0),
    "z-": (0, 0, -1, 0), "z+": (0, 0, 1, 0),
    "w-": (0, 0, 0, -1), "w+": (0, 0, 0, 1),
}

@dataclass(frozen=True, order=True)
class MeshAddress:
    space_id: str
    x: int
    y: int
    z: int
    w: int
    path: tuple[int, ...] = ()

    def __post_init__(self):
        if not isinstance(self.space_id, str) or not self.space_id.strip():
            raise ValueError("space_id must be a non-empty string")
        if any(type(v) is not int for v in (self.x, self.y, self.z, self.w)):
            raise ValueError("4D coordinates must be integers")
        if any(type(i) is not int or not 0 <= i < 343 for i in self.path):
            raise ValueError("nested path indices must be integers from 0 through 342")

    @property
    def coordinates(self):
        return (self.x, self.y, self.z, self.w)

    def neighbour(self, direction: str) -> "MeshAddress":
        if direction not in DIRECTIONS_4D:
            raise ValueError("unknown 4D direction")
        d = DIRECTIONS_4D[direction]
        return MeshAddress(self.space_id, *(a+b for a,b in zip(self.coordinates,d)), self.path)

    def child(self, index: int) -> "MeshAddress":
        if type(index) is not int or not 0 <= index < 343:
            raise ValueError("child index must be 0..342")
        return MeshAddress(self.space_id, *self.coordinates, self.path + (index,))

    def stable_id(self) -> str:
        data = {"space": self.space_id, "coords": self.coordinates, "path": self.path}
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        return sha256(b"PARADOX-4D-MESH-v1\\0" + raw).hexdigest()

    def to_dict(self):
        return {"space_id": self.space_id, "coordinates": list(self.coordinates),
                "path": list(self.path), "node_id": self.stable_id()}


def hyperblock_addresses(space_id: str, origin=(0,0,0,0)) -> Iterable[MeshAddress]:
    """Yield a 7^4 hyperblock: seven w-layers, each containing 343 xyz cells."""
    if len(origin) != 4 or any(type(v) is not int for v in origin):
        raise ValueError("origin must be four integers")
    ox, oy, oz, ow = origin
    for w in range(RADIX):
        for z in range(RADIX):
            for y in range(RADIX):
                for x in range(RADIX):
                    yield MeshAddress(space_id, ox+x, oy+y, oz+z, ow+w)


@dataclass(frozen=True)
class MeshLink:
    a: MeshAddress
    b: MeshAddress
    link_id: str
    authorized: bool
    verified: bool
    evidence_ref: str

    def __post_init__(self):
        if self.a == self.b:
            raise ValueError("self-links are not allowed")
        if not isinstance(self.link_id, str) or not self.link_id.strip():
            raise ValueError("link_id is required")
        if type(self.authorized) is not bool or type(self.verified) is not bool:
            raise ValueError("authorization and verification must be explicit booleans")
        if not isinstance(self.evidence_ref, str) or not self.evidence_ref.strip():
            raise ValueError("evidence_ref is required")
        if self.a.space_id != self.b.space_id and not (self.authorized and self.verified):
            raise PermissionError("cross-space bridge requires explicit authorization and verification")


class ParadoxMesh4D:
    """Undirected graph with deterministic BFS routing and append-only hash audit."""
    schema = "paradox-mesh-4d-v1"

    def __init__(self):
        self._nodes: set[MeshAddress] = set()
        self._links: dict[str, MeshLink] = {}
        self._adj: dict[MeshAddress, set[MeshAddress]] = {}
        self._audit: list[dict] = []
        self._audit_head = "0" * 64

    @property
    def node_count(self): return len(self._nodes)
    @property
    def link_count(self): return len(self._links)

    def _record(self, event):
        body = {"sequence": len(self._audit), "previous": self._audit_head, **event}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        digest = sha256(canonical).hexdigest()
        self._audit.append({**body, "hash": digest})
        self._audit_head = digest

    def add_node(self, node: MeshAddress):
        if not isinstance(node, MeshAddress): raise TypeError("node must be MeshAddress")
        if node not in self._nodes:
            self._nodes.add(node); self._adj[node] = set()
            self._record({"type": "node_added", "node": node.to_dict()})
        return node.stable_id()

    def add_link(self, link: MeshLink):
        if not isinstance(link, MeshLink): raise TypeError("link must be MeshLink")
        if link.link_id in self._links: raise ValueError("duplicate link_id")
        self.add_node(link.a); self.add_node(link.b)
        self._links[link.link_id] = link
        self._adj[link.a].add(link.b); self._adj[link.b].add(link.a)
        self._record({"type":"link_added", "link_id":link.link_id,
                      "a":link.a.to_dict(), "b":link.b.to_dict(),
                      "authorized":link.authorized, "verified":link.verified,
                      "evidence_ref":link.evidence_ref})
        return link.link_id

    def contains_node(self, address: MeshAddress) -> bool:
        return address in self._nodes

    def _edge_authorized(self, a: MeshAddress, b: MeshAddress) -> bool:
        return any(link.authorized and link.verified and
                   ((link.a == a and link.b == b) or (link.a == b and link.b == a))
                   for link in self._links.values())

    def route(self, source: MeshAddress, destination: MeshAddress):
        """Return shortest deterministic path, or None if no authorized path exists."""
        if source not in self._nodes or destination not in self._nodes: return None
        if source == destination: return (source,)
        queue = deque([source]); previous = {source: None}
        while queue:
            current = queue.popleft()
            for nxt in sorted(self._adj[current], key=lambda n: (n.space_id,n.coordinates,n.path)):
                if nxt in previous or not self._edge_authorized(current, nxt): continue
                previous[nxt] = current
                if nxt == destination:
                    path = [destination]
                    while path[-1] != source: path.append(previous[path[-1]])
                    return tuple(reversed(path))
                queue.append(nxt)
        return None

    def audit(self):
        """Return immutable copies; verify the hash-linked event sequence."""
        previous = "0" * 64
        for i, event in enumerate(self._audit):
            body = {k:v for k,v in event.items() if k != "hash"}
            if body["sequence"] != i or body["previous"] != previous:
                raise ValueError("audit sequence or predecessor mismatch")
            digest = sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            if digest != event["hash"]: raise ValueError("audit hash mismatch")
            previous = digest
        return tuple(dict(e) for e in self._audit)

    def manifest(self):
        return {"schema":self.schema, "dimensions":4, "parallel_spaces":"separate space_id namespaces",
                "block_shape":[7,7,7,7], "cells_per_hyperblock":BLOCK_4D_SIZE,
                "xyz_cells_per_w_layer":LAYER_3D_SIZE, "node_count":self.node_count,
                "link_count":self.link_count, "audit_events":len(self._audit),
                "audit_head":self._audit_head}
