"""Topology-aware 4D mesh fabric with authenticated neighbor links and hop forwarding."""
from __future__ import annotations
from dataclasses import dataclass
import secrets

from connection import MeshConnectionManager, MeshSession, PeerIdentity, ReplayCache
from mesh4d import MeshAddress, ParadoxMesh4D

@dataclass(frozen=True)
class MeshEndpoint:
    identity: PeerIdentity
    address: MeshAddress
    host: str
    port: int

    def __post_init__(self):
        if self.identity.address_id != self.address.stable_id():
            raise ValueError("peer identity address_id must equal the canonical 4D address")
        if not isinstance(self.host, str) or not self.host.strip():
            raise ValueError("endpoint host is required")
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError("endpoint port must be in 1..65535")

class MeshFabric:
    """Connects authorized topology neighbors and forwards payloads over verified routes.

    Every node needs the same approved topology and endpoint identity registry.
    Each hop is a separate mTLS session. This class does not start listeners.
    """
    ROUTE_TYPE = "PARADOX-MESH-ROUTE-v1"

    def __init__(self, local: MeshEndpoint, peers: dict[str, MeshEndpoint],
                 topology: ParadoxMesh4D, manager: MeshConnectionManager,
                 *, replay_cache: ReplayCache | None = None):
        if not isinstance(local, MeshEndpoint) or not isinstance(topology, ParadoxMesh4D):
            raise TypeError("local endpoint and ParadoxMesh4D topology are required")
        if manager.local != local.identity:
            raise ValueError("connection manager local identity mismatch")
        if set(peers) != set(manager.trusted_peers):
            raise ValueError("endpoint registry and TLS trust registry must contain the same peer IDs")
        endpoints = {local.identity.node_id: local}
        for node_id, endpoint in peers.items():
            if not isinstance(endpoint, MeshEndpoint) or node_id != endpoint.identity.node_id:
                raise ValueError("peer endpoint registry key mismatch")
            if endpoint.identity == local.identity:
                raise ValueError("local identity cannot also be a remote peer")
            if manager.trusted_peers[node_id] != endpoint.identity:
                raise ValueError("endpoint identity differs from TLS trust registry")
            endpoints[node_id] = endpoint
        if len({e.address for e in endpoints.values()}) != len(endpoints):
            raise ValueError("each node must have a unique 4D address")
        if any(not topology.contains_node(e.address) for e in endpoints.values()):
            raise ValueError("every registered endpoint must exist in the 4D topology")
        self.local, self.peers, self.topology = local, dict(peers), topology
        self.manager, self.replay_cache = manager, replay_cache or ReplayCache()
        self._endpoints = endpoints
        self._by_address = {e.address: node_id for node_id, e in endpoints.items()}
        self._sessions: dict[str, MeshSession] = {}

    def _direct_link(self, first_id: str, second_id: str) -> bool:
        first, second = self._endpoints.get(first_id), self._endpoints.get(second_id)
        if first is None or second is None:
            return False
        return self.topology.route(first.address, second.address) == (first.address, second.address)

    def route_to(self, destination_id: str) -> tuple[str, ...]:
        if destination_id not in self._endpoints:
            raise KeyError("destination is not registered in this mesh")
        addresses = self.topology.route(self.local.address, self._endpoints[destination_id].address)
        if addresses is None:
            raise ConnectionError("no authorized and verified 4D route")
        try:
            return tuple(self._by_address[address] for address in addresses)
        except KeyError as exc:
            raise ConnectionError("route contains an endpoint missing from the trust registry") from exc

    def attach_session(self, peer_id: str, session: MeshSession) -> None:
        peer = self.peers.get(peer_id)
        if peer is None or session.peer != peer.identity:
            raise PermissionError("session peer is not the registered node")
        if not self._direct_link(self.local.identity.node_id, peer_id):
            raise PermissionError("session is not an authorized direct 4D neighbor")
        self._sessions[peer_id] = session

    def connect_peer(self, peer_id: str, client_context) -> MeshSession:
        peer = self.peers.get(peer_id)
        if peer is None:
            raise KeyError("peer is not registered")
        if not self._direct_link(self.local.identity.node_id, peer_id):
            raise PermissionError("peer is not an authorized direct 4D neighbor")
        session = self.manager.connect(peer_id, peer.host, peer.port, client_context)
        self.attach_session(peer_id, session)
        return session

    def connect_neighbors(self, client_context) -> tuple[str, ...]:
        """Dial every registered, authorized direct neighbor; fail on first error."""
        connected = []
        for peer_id in sorted(self.peers):
            if self._direct_link(self.local.identity.node_id, peer_id):
                self.connect_peer(peer_id, client_context)
                connected.append(peer_id)
        return tuple(connected)

    def send_to(self, destination_id: str, payload: dict) -> str:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a JSON object")
        route = self.route_to(destination_id)
        if len(route) < 2:
            raise ValueError("destination is the local node")
        next_hop = route[1]
        session = self._sessions.get(next_hop)
        if session is None:
            raise ConnectionError("next-hop connection is not established")
        message_id = secrets.token_hex(16)
        envelope = {"type": self.ROUTE_TYPE, "source": route[0], "destination": route[-1],
                    "route": list(route), "hop_index": 0, "ttl": len(route)-1,
                    "message_id": message_id, "payload": payload}
        session.send(envelope)
        return message_id

    def receive_from(self, incoming_peer_id: str):
        """Receive one routed envelope; return payload at destination, otherwise forward it."""
        session = self._sessions.get(incoming_peer_id)
        if session is None:
            raise ConnectionError("incoming peer session is not established")
        envelope = session.receive()
        if not isinstance(envelope, dict) or envelope.get("type") != self.ROUTE_TYPE:
            raise ValueError("unsupported mesh fabric envelope")
        route = envelope.get("route")
        if not isinstance(route, list) or not 2 <= len(route) <= len(self._endpoints):
            raise ValueError("invalid mesh route")
        if len(set(route)) != len(route) or route[0] != envelope.get("source") or route[-1] != envelope.get("destination"):
            raise PermissionError("mesh route endpoints or loop check failed")
        hop = envelope.get("hop_index")
        ttl = envelope.get("ttl")
        if type(hop) is not int or not 0 <= hop < len(route)-1:
            raise PermissionError("invalid route hop index")
        if type(ttl) is not int or ttl != len(route)-1-hop:
            raise PermissionError("route TTL mismatch")
        if route[hop] != incoming_peer_id or route[hop+1] != self.local.identity.node_id:
            raise PermissionError("route does not match authenticated incoming peer")
        message_id = envelope.get("message_id")
        if not isinstance(message_id, str) or len(message_id) != 32:
            raise ValueError("invalid routed message ID")
        try: int(message_id, 16)
        except ValueError as exc: raise ValueError("invalid routed message ID") from exc
        if not self.replay_cache.accept_once(f"fabric:{envelope['source']}:{message_id}"):
            raise PermissionError("routed message replayed")
        for left, right in zip(route, route[1:]):
            if not self._direct_link(left, right):
                raise PermissionError("route contains an unverified or unauthorized 4D link")
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("routed payload must be a JSON object")
        if route[hop+1] == envelope["destination"]:
            return payload
        next_hop = route[hop+2]
        outgoing = self._sessions.get(next_hop)
        if outgoing is None:
            raise ConnectionError("next-hop connection is not established")
        forwarded = dict(envelope)
        forwarded["hop_index"] = hop + 1
        forwarded["ttl"] = ttl - 1
        outgoing.send(forwarded)
        return None

    def close(self) -> None:
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
