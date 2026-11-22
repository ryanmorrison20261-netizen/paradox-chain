"""Strict DER ECDSA secp256k1 threshold authentication primitives.

This module deliberately does not implement Coinbase credentials or submit transactions.
It verifies an application-level request envelope before a separately configured CDP client.
"""
from __future__ import annotations
import hashlib, threading, time
from dataclasses import dataclass
from typing import Mapping, Sequence
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

class AuthError(ValueError):
    """Invalid or replayed authentication request."""

@dataclass(frozen=True)
class RequestEnvelope:
    method: str
    path: str
    timestamp: int
    nonce: str
    body: bytes

    def message(self) -> bytes:
        method = self.method.upper()
        if not method.isascii() or not method.isalpha():
            raise AuthError("invalid HTTP method")
        if not self.path.startswith("/") or "\n" in self.path:
            raise AuthError("invalid request path")
        if not self.nonce or len(self.nonce) > 128 or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in self.nonce
        ):
            raise AuthError("invalid nonce")
        body_hash = hashlib.sha256(self.body).hexdigest()
        return f"PARADOX-REQ-v1\n{method}\n{self.path}\n{self.timestamp}\n{self.nonce}\n{body_hash}".encode("ascii")

class NonceStore:
    """Thread-safe process-local replay guard.

    Production multi-worker deployments MUST replace this with a shared atomic store
    (for example Redis SET NX with expiry); this in-memory implementation is for tests
    and single-process deployments only.
    """
    def __init__(self):
        self._seen = {}
        self._lock = threading.Lock()

    def consume_many(self, signers: Sequence[str], nonce: str, expires_at: int, now: int) -> bool:
        keys = [(signer, nonce) for signer in signers]
        with self._lock:
            self._seen = {k: v for k, v in self._seen.items() if v >= now}
            if any(k in self._seen for k in keys):
                return False
            for key in keys:
                self._seen[key] = expires_at
            return True

def load_secp256k1_public_key(pem: bytes):
    key = serialization.load_pem_public_key(pem)
    if not isinstance(key, ec.EllipticCurvePublicKey) or key.curve.name != "secp256k1":
        raise AuthError("signer key must be secp256k1")
    return key

def verify_der_signature(public_key, message: bytes, signature_der: bytes) -> bool:
    """Verify canonical ASN.1 DER ECDSA/SHA-256; reject malformed/non-canonical scalars."""
    if not isinstance(signature_der, bytes) or not (8 <= len(signature_der) <= 72):
        return False
    try:
        r, s = decode_dss_signature(signature_der)
        if encode_dss_signature(r, s) != signature_der:
            return False
        if not (1 <= r < SECP256K1_ORDER and 1 <= s < SECP256K1_ORDER):
            return False
        public_key.verify(signature_der, message, ec.ECDSA(hashes.SHA256()))
        return True
    except (ValueError, InvalidSignature):
        return False

def verify_threshold(
    envelope: RequestEnvelope,
    signatures: Mapping[str, bytes],
    trusted_keys: Mapping[str, bytes],
    threshold: int,
    nonce_store: NonceStore,
    *,
    now: int | None = None,
    max_skew_seconds: int = 300,
) -> tuple[bool, list[str]]:
    """Verify distinct configured signers, then atomically consume nonce on threshold success."""
    now = int(time.time()) if now is None else int(now)
    if not 1 <= threshold <= len(trusted_keys):
        raise AuthError("threshold outside signer set")
    if abs(now - envelope.timestamp) > max_skew_seconds:
        raise AuthError("request timestamp outside allowed window")
    message = envelope.message()
    accepted = []
    for signer, signature in signatures.items():
        if signer not in trusted_keys:
            continue
        public_key = load_secp256k1_public_key(trusted_keys[signer])
        if verify_der_signature(public_key, message, signature):
            accepted.append(signer)
    if len(accepted) < threshold:
        return False, accepted
    if not nonce_store.consume_many(
        accepted, envelope.nonce, envelope.timestamp + max_skew_seconds, now
    ):
        raise AuthError("replayed request nonce")
    return True, accepted
