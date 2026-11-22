"""Opt-in C4 peer transport: mutual TLS, pinned identities, bounded frames and replay guards."""
from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
import json, secrets, socket, ssl, struct, threading, time

PROTOCOL = "PARADOX-MESH-CONNECTION-v1"
MAX_FRAME_BYTES = 1_048_576

def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def _recv_exact(sock, size):
    chunks = []
    while size:
        part = sock.recv(size)
        if not part: raise ConnectionError("peer closed during frame")
        chunks.append(part); size -= len(part)
    return b"".join(chunks)

def send_frame(sock, value, *, max_bytes=MAX_FRAME_BYTES):
    if not isinstance(value, dict): raise TypeError("frame must be a JSON object")
    body = _canonical(value)
    if not body or len(body) > max_bytes: raise ValueError("frame exceeds size limit")
    sock.sendall(struct.pack("!I", len(body)) + body)

def receive_frame(sock, *, max_bytes=MAX_FRAME_BYTES):
    size = struct.unpack("!I", _recv_exact(sock, 4))[0]
    if size == 0 or size > max_bytes: raise ValueError("invalid frame length")
    try: value = json.loads(_recv_exact(sock, size).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise ValueError("invalid JSON frame") from exc
    if not isinstance(value, dict): raise ValueError("frame must be a JSON object")
    return value

@dataclass(frozen=True)
class PeerIdentity:
    node_id: str
    address_id: str
    certificate_sha256: str
    def __post_init__(self):
        if not self.node_id or not self.address_id: raise ValueError("node_id and address_id required")
        fp = self.certificate_sha256.lower().replace(":", "")
        if len(fp) != 64 or any(c not in "0123456789abcdef" for c in fp):
            raise ValueError("certificate_sha256 must be a SHA-256 hex fingerprint")
        object.__setattr__(self, "certificate_sha256", fp)

class ReplayCache:
    def __init__(self, *, ttl=600.0, max_entries=100_000):
        if ttl <= 0 or max_entries < 1: raise ValueError("invalid replay-cache limits")
        self.ttl, self.max_entries = float(ttl), int(max_entries)
        self._items, self._lock = OrderedDict(), threading.Lock()
    def accept_once(self, token, *, now=None):
        if not isinstance(token, str) or not token or len(token) > 128: return False
        current = time.monotonic() if now is None else now
        with self._lock:
            while self._items and next(iter(self._items.values())) <= current: self._items.popitem(last=False)
            if token in self._items: return False
            while len(self._items) >= self.max_entries: self._items.popitem(last=False)
            self._items[token] = current + self.ttl
            return True

class MeshSession:
    def __init__(self, tls_socket, local, trusted_peers, replay_cache, *, max_frame_bytes=MAX_FRAME_BYTES):
        if not 256 <= max_frame_bytes <= MAX_FRAME_BYTES: raise ValueError("frame limit must be 256 bytes..1 MiB")
        self._socket, self.local = tls_socket, local
        self.trusted_peers, self.replay_cache = dict(trusted_peers), replay_cache
        self.max_frame_bytes, self.peer = max_frame_bytes, None
        self._send_sequence = self._receive_sequence = 0
        self._established, self._send_lock = False, threading.Lock()

    def establish(self, *, expected_peer_id=None):
        if self._established: raise RuntimeError("session already established")
        cert = self._socket.getpeercert(binary_form=True)
        if not cert: raise PermissionError("TLS peer certificate missing")
        hello = {"protocol": PROTOCOL, "node_id": self.local.node_id,
                 "address_id": self.local.address_id, "nonce": secrets.token_hex(32)}
        send_frame(self._socket, hello, max_bytes=self.max_frame_bytes)
        remote = receive_frame(self._socket, max_bytes=self.max_frame_bytes)
        if remote.get("protocol") != PROTOCOL: raise PermissionError("unsupported mesh protocol")
        peer_id = remote.get("node_id")
        peer = self.trusted_peers.get(peer_id)
        if peer is None: raise PermissionError("peer identity not trusted")
        if expected_peer_id is not None and peer_id != expected_peer_id: raise PermissionError("connected peer differs from requested node")
        if remote.get("address_id") != peer.address_id: raise PermissionError("peer 4D address mismatch")
        if not secrets.compare_digest(sha256(cert).hexdigest(), peer.certificate_sha256):
            raise PermissionError("peer TLS certificate fingerprint mismatch")
        nonce = remote.get("nonce")
        if not isinstance(nonce, str) or len(nonce) != 64: raise PermissionError("invalid peer handshake nonce")
        try: int(nonce, 16)
        except ValueError as exc: raise PermissionError("invalid peer handshake nonce") from exc
        if not self.replay_cache.accept_once(f"hello:{peer_id}:{nonce}"): raise PermissionError("replayed peer handshake")
        self.peer, self._established = peer, True
        return peer

    def send(self, payload):
        if not self._established or self.peer is None: raise ConnectionError("session is not authenticated")
        if not isinstance(payload, dict): raise TypeError("payload must be a JSON object")
        with self._send_lock:
            self._send_sequence += 1
            frame = {"protocol": PROTOCOL, "sender": self.local.node_id, "recipient": self.peer.node_id,
                     "sequence": self._send_sequence, "message_id": secrets.token_hex(16), "payload": payload}
            send_frame(self._socket, frame, max_bytes=self.max_frame_bytes)
            return self._send_sequence

    def receive(self):
        if not self._established or self.peer is None: raise ConnectionError("session is not authenticated")
        frame = receive_frame(self._socket, max_bytes=self.max_frame_bytes)
        if frame.get("protocol") != PROTOCOL: raise PermissionError("unsupported mesh message protocol")
        if frame.get("sender") != self.peer.node_id or frame.get("recipient") != self.local.node_id:
            raise PermissionError("mesh message endpoint mismatch")
        seq = frame.get("sequence")
        if type(seq) is not int or seq != self._receive_sequence + 1: raise PermissionError("mesh sequence invalid or replayed")
        mid, payload = frame.get("message_id"), frame.get("payload")
        if not isinstance(mid, str) or len(mid) != 32: raise PermissionError("invalid message id")
        if not self.replay_cache.accept_once(f"message:{self.peer.node_id}:{mid}"): raise PermissionError("replayed mesh message")
        if not isinstance(payload, dict): raise ValueError("payload must be a JSON object")
        self._receive_sequence = seq
        return payload

    def close(self):
        try: self._socket.shutdown(socket.SHUT_RDWR)
        except (OSError, AttributeError): pass
        self._socket.close(); self._established = False

class MeshConnectionManager:
    """TLS 1.3 mTLS dialer/acceptor. Networking is disabled unless explicitly enabled."""
    def __init__(self, local, trusted_peers, *, enabled=False, replay_cache=None, timeout=5.0, max_frame_bytes=MAX_FRAME_BYTES):
        if not isinstance(local, PeerIdentity): raise TypeError("local identity required")
        if local.node_id in trusted_peers: raise ValueError("local node cannot be a remote peer")
        if not 0 < timeout <= 60: raise ValueError("timeout must be in (0, 60]")
        self.local, self.trusted_peers, self.enabled = local, dict(trusted_peers), bool(enabled)
        self.replay_cache = replay_cache or ReplayCache()
        self.timeout, self.max_frame_bytes = float(timeout), max_frame_bytes

    @staticmethod
    def _check_context(ctx, *, server):
        if not isinstance(ctx, ssl.SSLContext): raise TypeError("operator-configured SSLContext required")
        if ctx.minimum_version < ssl.TLSVersion.TLSv1_3: raise ValueError("TLS 1.3 minimum required")
        if ctx.verify_mode != ssl.CERT_REQUIRED: raise ValueError("CERT_REQUIRED mutual TLS is required")
        if not server and not ctx.check_hostname: raise ValueError("client hostname verification required")

    def connect(self, peer_id, host, port, context):
        if not self.enabled: raise PermissionError("mesh networking disabled")
        if peer_id not in self.trusted_peers: raise PermissionError("requested peer not trusted")
        self._check_context(context, server=False)
        raw = socket.create_connection((host, port), timeout=self.timeout)
        try:
            raw.settimeout(self.timeout)
            tls = context.wrap_socket(raw, server_hostname=host)
            session = MeshSession(tls, self.local, self.trusted_peers, self.replay_cache, max_frame_bytes=self.max_frame_bytes)
            session.establish(expected_peer_id=peer_id)
            return session
        except Exception:
            raw.close(); raise

    def accept_one(self, listener, context):
        if not self.enabled: raise PermissionError("mesh networking disabled")
        self._check_context(context, server=True)
        raw, _ = listener.accept()
        try:
            raw.settimeout(self.timeout)
            tls = context.wrap_socket(raw, server_side=True)
            session = MeshSession(tls, self.local, self.trusted_peers, self.replay_cache, max_frame_bytes=self.max_frame_bytes)
            session.establish()
            return session
        except Exception:
            raw.close(); raise
