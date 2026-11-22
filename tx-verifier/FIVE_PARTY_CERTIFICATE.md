# Paradox 5-of-5 DER evidence certificate

## Protocol

- Protocol ID: `PARADOX-MULTIAUTH-5OF5-v1`
- Evidence digest: SHA-256 over deterministic UTF-8 JSON (sorted object keys, compact separators, no floats; exact decimals must be strings).
- Signing input: `PARADOX-MULTIAUTH-CERTIFICATE\\0` followed by canonical JSON containing protocol version, evidence SHA-256, nonce, and Unix timestamp.
- Signature: ASN.1 DER ECDSA over secp256k1 with SHA-256.
- Threshold: exactly five distinct, configured signer identities and five distinct public-key fingerprints.
- Replay protection: transactional SQLite unique nonce store. All verifier workers must share the same database. Multi-host deployments must use a shared transactional database with equivalent atomic uniqueness.
- Clock policy: default maximum absolute clock skew is 300 seconds.

This canonicalization is the protocol's explicitly defined JSON profile; it is not claimed to implement RFC 8785/JCS. Producers must use the same profile and reject floats.

## Signer registry

The caller must provision five trusted public keys out-of-band and map them to these role labels (or another controlled five-name registry):

1. `primary`
2. `o2`
3. `guardian`
4. `chain_auditor`
5. `adversarial_auditor`

The verifier rejects missing or unexpected signer names, non-secp256k1 keys, duplicate public-key fingerprints, invalid DER signatures, altered evidence/envelope fields, expired timestamps, and replayed nonces. It consumes the nonce only after all five signatures verify.

## Use

The verifier intentionally does not create signatures or manage private keys. Each participant must sign the exact `signing_message(EvidenceEnvelope(...))` bytes using their own approved signer. Supply those DER byte strings and the independently provisioned trusted public keys to `verify_five_party_certificate`.

Example invocation (key loading and signature collection are deployment-specific):

```python
from five_party_certificate import (
    EvidenceEnvelope, SQLiteReplayStore, verify_five_party_certificate
)

envelope = EvidenceEnvelope(
    evidence=canonical_evidence_object,
    nonce=cryptographically_random_url_safe_nonce,
    timestamp=current_unix_timestamp,
)
certificate = verify_five_party_certificate(
    envelope,
    signatures=five_der_signatures_by_signer_name,
    trusted_keys_pem=five_trusted_public_keys_pem,
    replay_store=SQLiteReplayStore("/var/lib/paradox/used-nonces.sqlite"),
)
```

## Certificate contents

A successful certificate includes the protocol version, canonical evidence digest, nonce, timestamp, verification time, 5-of-5 status, and for each signer: identity label, SHA-256 public-key fingerprint, DER signature hex, signature SHA-256, format, and verification result.

A generated unit-test certificate is test-only evidence. It is not an approval by o², Guardian, or any real-world auditor. The production certificate remains **PENDING** until all five real participants sign the same evidence digest and their signatures are verified.

## Primary signer proof-of-possession update (2026-11-21)

The supplied DER signature was independently verified against the registered public key and the exact challenge message using ECDSA/secp256k1 with SHA-256.

- Public-key fingerprint: `f1c3845a538c953bea0534a7de90acebfc03212cc6f3e7a350deb70ebbbb14d7`
- Challenge nonce: `Foj1NI2a29R7fY-M8ziVu85ga9yCiSWv`
- Challenge timestamp: `1795319431` (2026-11-22T03:50:31Z)
- Verification time: `2026-11-21T20:51:14-07:00`
- Proof of private-key possession: **PASS**
- Independent binding of this key to the Primary signer identity/role: **PENDING**
- Trusted for 5-of-5 authorization: **NO** until identity/role binding is independently established.

The signature and challenge transcript are recorded in `trust/primary-public-key.json`. This proves control of the key for the challenge; it does not by itself prove the real-world identity or authority of the signer.
