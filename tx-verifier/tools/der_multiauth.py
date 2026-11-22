"""Strict DER ECDSA secp256k1 threshold authentication primitives.

This module deliberately does not implement Coinbase credentials or submit transactions.
It verifies an application-level request envelope before a separately configured CDP client.
"""
from __future__ import annotations
import hashlib, threading, time
from dataclasses import dataclass
from typing import Mapping
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
        if not self.path.startswith("/") or "\n" in self.path or "\r" in self.path:
            raise AuthError("invalid request path")
        if (not isinstance(self.timestamp, int) or isinstance(self.timestamp, bool)
                or self.timestamp < 0):
            raise AuthError("invalid request timestamp")
        if (not isinstance(self.nonce, str) or not (16 <= len(self.nonce) <= 128)
                or not self.nonce.isascii() or any(
                    c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                    for c in self.nonce
                )):
            raise AuthError("nonce must be 16 to 128 URL-safe ASCII characters")
        if not isinstance(self.body, bytes):
            raise AuthError("request body must be bytes")
        body_hash = hashlib.sha256(self.body).hexdigest()
        return f"PARADOX-REQ-v1\n{method}\n{self.path}\n{self.timestamp}\n{self.nonce}\n{body_hash}".encode("ascii")

class NonceStore:
    """Thread-safe process-local, request-wide replay guard.

    Production multi-worker deployments MUST replace this with a shared atomic store
    (for example Redis SET NX with expiry); this in-memory implementation is for tests
    and single-process deployments only. A nonce is consumed globally, not per signer.
    """
    def __init__(self):
        self._seen = {}
        self._lock = threading.Lock()

    def consume(self, nonce: str, expires_at: int, now: int) -> bool:
        with self._lock:
            self._seen = {key: expiry for key, expiry in self._seen.items() if expiry >= now}
            if nonce in self._seen:
                return False
            self._seen[nonce] = expires_at
            return True

def load_secp256k1_public_key(pem: bytes):
    try:
        key = serialization.load_pem_public_key(pem)
    except (TypeError, ValueError) as exc:
        raise AuthError("invalid signer public key") from exc
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
    """Verify distinct configured signers, then atomically consume one request nonce."""
    now = int(time.time()) if now is None else int(now)
    if not 1 <= threshold <= len(trusted_keys):
        raise AuthError("threshold outside signer set")
    if not isinstance(max_skew_seconds, int) or max_skew_seconds < 0:
        raise AuthError("max_skew_seconds must be a non-negative integer")
    if abs(now - envelope.timestamp) > max_skew_seconds:
        raise AuthError("request timestamp outside allowed window")
    unexpected = set(signatures) - set(trusted_keys)
    if unexpected:
        raise AuthError(f"untrusted signer identities: {sorted(unexpected)}")

    message = envelope.message()
    loaded = {name: load_secp256k1_public_key(pem) for name, pem in trusted_keys.items()}
    fingerprints = {
        name: hashlib.sha256(key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )).hexdigest()
        for name, key in loaded.items()
    }
    if len(set(fingerprints.values())) != len(loaded):
        raise AuthError("duplicate trusted public key: each signer identity must have a distinct key")

    accepted = [
        signer for signer, signature in signatures.items()
        if verify_der_signature(loaded[signer], message, signature)
    ]
    if len(accepted) < threshold:
        return False, accepted
    if not nonce_store.consume(
        envelope.nonce, envelope.timestamp + max_skew_seconds, now
    ):
        raise AuthError("replayed request nonce")
    return True, accepted
