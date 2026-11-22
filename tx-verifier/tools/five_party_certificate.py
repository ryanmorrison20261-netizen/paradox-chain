"""Five-party canonical evidence certification using DER ECDSA/secp256k1.

All five trusted signers sign the same domain-separated digest envelope.
No signing/private-key functionality is provided: callers supply signatures.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

PROTOCOL_VERSION = "PARADOX-MULTIAUTH-5OF5-v1"
DOMAIN = b"PARADOX-MULTIAUTH-CERTIFICATE\x00"
EXPECTED_SIGNER_COUNT = 5
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


class CertificateError(ValueError):
    """Malformed, incomplete, invalid, expired, or replayed certificate."""


class ReplayStore(Protocol):
    def consume(self, nonce: str, expires_at: int, now: int) -> bool: ...


class SQLiteReplayStore:
    """Persistent, transactional replay store. Share the DB across workers.

    For multi-host deployments, use a shared transactional database with an
    equivalent unique constraint; do not use per-process memory.
    """
    def __init__(self, database: str | Path):
        self.database = str(database)
        with sqlite3.connect(self.database) as db:
            db.execute("CREATE TABLE IF NOT EXISTS consumed_nonces (nonce TEXT PRIMARY KEY, expires_at INTEGER NOT NULL)")

    def consume(self, nonce: str, expires_at: int, now: int) -> bool:
        with sqlite3.connect(self.database, timeout=30, isolation_level="IMMEDIATE") as db:
            db.execute("DELETE FROM consumed_nonces WHERE expires_at < ?", (now,))
            try:
                db.execute("INSERT INTO consumed_nonces(nonce, expires_at) VALUES (?, ?)", (nonce, expires_at))
            except sqlite3.IntegrityError:
                return False
            return True


@dataclass(frozen=True)
class EvidenceEnvelope:
    evidence: object
    nonce: str
    timestamp: int
    protocol_version: str = PROTOCOL_VERSION


def canonical_json(value: object) -> bytes:
    """Deterministic UTF-8 JSON; deliberately rejects floats and non-JSON types."""
    def validate(item):
        if item is None or isinstance(item, (str, bool, int)):
            return
        if isinstance(item, float):
            raise CertificateError("floating-point values are forbidden; encode exact decimals as strings")
        if isinstance(item, list):
            for child in item:
                validate(child)
            return
        if isinstance(item, dict):
            if any(not isinstance(k, str) for k in item):
                raise CertificateError("evidence object keys must be strings")
            for child in item.values():
                validate(child)
            return
        raise CertificateError(f"unsupported evidence value type: {type(item).__name__}")
    validate(value)
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise CertificateError("evidence cannot be canonicalized") from exc


def evidence_digest(evidence: object) -> str:
    return hashlib.sha256(canonical_json(evidence)).hexdigest()


def signing_message(envelope: EvidenceEnvelope) -> bytes:
    if envelope.protocol_version != PROTOCOL_VERSION:
        raise CertificateError("unsupported protocol version")
    if not isinstance(envelope.nonce, str) or not (16 <= len(envelope.nonce) <= 128):
        raise CertificateError("nonce must contain 16 to 128 characters")
    if not envelope.nonce.isascii() or not all(c.isalnum() or c in "-_" for c in envelope.nonce):
        raise CertificateError("nonce must be URL-safe ASCII")
    if not isinstance(envelope.timestamp, int) or isinstance(envelope.timestamp, bool) or envelope.timestamp < 0:
        raise CertificateError("timestamp must be a non-negative integer")
    body = {
        "protocol_version": envelope.protocol_version,
        "evidence_sha256": evidence_digest(envelope.evidence),
        "nonce": envelope.nonce,
        "timestamp": envelope.timestamp,
    }
    return DOMAIN + canonical_json(body)


def _load_key(pem: bytes):
    try:
        key = serialization.load_pem_public_key(pem)
    except (ValueError, TypeError) as exc:
        raise CertificateError("invalid signer public key") from exc
    if not isinstance(key, ec.EllipticCurvePublicKey) or key.curve.name != "secp256k1":
        raise CertificateError("all signer keys must be secp256k1")
    return key


def _fingerprint(key) -> str:
    der = key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return hashlib.sha256(der).hexdigest()


def _verify(key, message: bytes, signature: bytes) -> bool:
    if not isinstance(signature, bytes) or not 8 <= len(signature) <= 72:
        return False
    try:
        r, s = decode_dss_signature(signature)
        if encode_dss_signature(r, s) != signature:
            return False
        if not (1 <= r < SECP256K1_ORDER and 1 <= s < SECP256K1_ORDER):
            return False
        key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except (ValueError, InvalidSignature):
        return False


def verify_five_party_certificate(
    envelope: EvidenceEnvelope,
    signatures: Mapping[str, bytes],
    trusted_keys_pem: Mapping[str, bytes],
    replay_store: ReplayStore,
    *,
    now: int | None = None,
    max_skew_seconds: int = 300,
) -> dict:
    """Verify exactly five distinct trusted signers and return a certificate.

    Nonce is consumed only after all five signatures pass. The replay store must
    provide an atomic insert/unique constraint shared by every verifier instance.
    """
    now = int(time.time()) if now is None else int(now)
    if len(trusted_keys_pem) != EXPECTED_SIGNER_COUNT:
        raise CertificateError("trusted signer set must contain exactly five identities")
    if set(signatures) != set(trusted_keys_pem):
        missing = sorted(set(trusted_keys_pem) - set(signatures))
        unexpected = sorted(set(signatures) - set(trusted_keys_pem))
        raise CertificateError(f"signer set mismatch; missing={missing}; unexpected={unexpected}")
    if abs(now - envelope.timestamp) > max_skew_seconds:
        raise CertificateError("certificate timestamp expired or outside allowed clock skew")

    message = signing_message(envelope)
    loaded = {name: _load_key(pem) for name, pem in trusted_keys_pem.items()}
    fingerprints = {name: _fingerprint(key) for name, key in loaded.items()}
    if len(set(fingerprints.values())) != EXPECTED_SIGNER_COUNT:
        raise CertificateError("duplicate public-key fingerprint: signer identities must have distinct keys")

    results = []
    for name in sorted(loaded):
        valid = _verify(loaded[name], message, signatures[name])
        results.append({
            "signer": name,
            "public_key_fingerprint_sha256": fingerprints[name],
            "signature_format": "ASN.1 DER ECDSA/secp256k1/SHA-256",
            "signature_der_hex": signatures[name].hex(),
            "signature_sha256": hashlib.sha256(signatures[name]).hexdigest(),
            "valid": valid,
        })
    if not all(item["valid"] for item in results):
        raise CertificateError("one or more signer signatures are invalid")
    if not replay_store.consume(envelope.nonce, envelope.timestamp + max_skew_seconds, now):
        raise CertificateError("replayed nonce")

    return {
        "certificate_type": "PARADOX-5-PARTY-MULTIAUTH",
        "protocol_version": envelope.protocol_version,
        "evidence_sha256": evidence_digest(envelope.evidence),
        "evidence_canonicalization": "UTF-8 JSON; sorted keys; compact separators; floats forbidden",
        "nonce": envelope.nonce,
        "timestamp": envelope.timestamp,
        "verified_at": now,
        "threshold": "5-of-5",
        "status": "PASS",
        "signers": results,
    }
