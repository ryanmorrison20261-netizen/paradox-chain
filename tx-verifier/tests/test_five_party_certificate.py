import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from five_party_certificate import (
    CertificateError, EvidenceEnvelope, SQLiteReplayStore,
    canonical_json, evidence_digest, signing_message,
    verify_five_party_certificate,
)


class FivePartyCertificateTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000
        self.names = ("primary", "o2", "guardian", "chain_auditor", "adversarial_auditor")
        self.private = {n: ec.generate_private_key(ec.SECP256K1()) for n in self.names}
        self.public = {
            n: k.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ) for n, k in self.private.items()
        }
        self.evidence = {
            "project": "MetaParadox",
            "claims": ["ledger-signatures", "guardian-auth", "neo-proof"],
            "sequence": 7,
        }
        self.envelope = EvidenceEnvelope(
            self.evidence, "nonce-0123456789abcdef", self.now
        )
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteReplayStore(os.path.join(self.temp.name, "replay.sqlite"))

    def tearDown(self):
        self.temp.cleanup()

    def signatures(self, envelope=None):
        msg = signing_message(envelope or self.envelope)
        return {n: k.sign(msg, ec.ECDSA(hashes.SHA256())) for n, k in self.private.items()}

    def test_valid_5_of_5_certificate(self):
        cert = verify_five_party_certificate(
            self.envelope, self.signatures(), self.public, self.store, now=self.now
        )
        self.assertEqual(cert["status"], "PASS")
        self.assertEqual(cert["threshold"], "5-of-5")
        self.assertEqual(len(cert["signers"]), 5)
        self.assertTrue(all(s["valid"] for s in cert["signers"]))
        self.assertEqual(cert["evidence_sha256"], evidence_digest(self.evidence))

    def test_canonicalization_ignores_object_key_order(self):
        self.assertEqual(canonical_json({"b": 2, "a": 1}), canonical_json({"a": 1, "b": 2}))
        self.assertEqual(evidence_digest({"b": 2, "a": 1}), evidence_digest({"a": 1, "b": 2}))

    def test_missing_signer_rejected(self):
        sigs = self.signatures()
        sigs.pop("guardian")
        with self.assertRaisesRegex(CertificateError, "signer set mismatch"):
            verify_five_party_certificate(self.envelope, sigs, self.public, self.store, now=self.now)

    def test_unexpected_signer_rejected(self):
        sigs = self.signatures()
        sigs["impostor"] = sigs.pop("primary")
        with self.assertRaises(CertificateError):
            verify_five_party_certificate(self.envelope, sigs, self.public, self.store, now=self.now)

    def test_duplicate_public_key_rejected(self):
        duplicate = dict(self.public)
        duplicate["guardian"] = duplicate["o2"]
        with self.assertRaisesRegex(CertificateError, "duplicate public-key"):
            verify_five_party_certificate(self.envelope, self.signatures(), duplicate, self.store, now=self.now)

    def test_invalid_signature_rejected(self):
        sigs = self.signatures()
        sigs["guardian"] = b"not-a-DER-signature"
        with self.assertRaisesRegex(CertificateError, "signatures are invalid"):
            verify_five_party_certificate(self.envelope, sigs, self.public, self.store, now=self.now)

    def test_tampered_evidence_rejected(self):
        altered = EvidenceEnvelope({**self.evidence, "sequence": 8}, self.envelope.nonce, self.now)
        with self.assertRaisesRegex(CertificateError, "signatures are invalid"):
            verify_five_party_certificate(altered, self.signatures(), self.public, self.store, now=self.now)

    def test_nonce_timestamp_protocol_and_digest_are_bound(self):
        changed_nonce = EvidenceEnvelope(self.evidence, "nonce-xxxxxxxxxxxxxxxx", self.now)
        with self.assertRaisesRegex(CertificateError, "signatures are invalid"):
            verify_five_party_certificate(changed_nonce, self.signatures(), self.public, self.store, now=self.now)
        changed_time = EvidenceEnvelope(self.evidence, self.envelope.nonce, self.now + 1)
        with self.assertRaisesRegex(CertificateError, "signatures are invalid"):
            verify_five_party_certificate(changed_time, self.signatures(), self.public, self.store, now=self.now)

    def test_expired_timestamp_rejected(self):
        with self.assertRaisesRegex(CertificateError, "timestamp expired"):
            verify_five_party_certificate(
                self.envelope, self.signatures(), self.public, self.store,
                now=self.now + 301,
            )

    def test_replay_rejected(self):
        sigs = self.signatures()
        verify_five_party_certificate(self.envelope, sigs, self.public, self.store, now=self.now)
        with self.assertRaisesRegex(CertificateError, "replayed nonce"):
            verify_five_party_certificate(self.envelope, sigs, self.public, self.store, now=self.now)

    def test_nonce_not_consumed_on_failed_signature(self):
        sigs = self.signatures()
        sigs["guardian"] = b"bad"
        with self.assertRaises(CertificateError):
            verify_five_party_certificate(self.envelope, sigs, self.public, self.store, now=self.now)
        valid = verify_five_party_certificate(
            self.envelope, self.signatures(), self.public, self.store, now=self.now
        )
        self.assertEqual(valid["status"], "PASS")

    def test_floats_rejected_from_canonical_evidence(self):
        with self.assertRaisesRegex(CertificateError, "floating-point"):
            canonical_json({"amount": 1.25})

    def test_wrong_curve_rejected(self):
        bad = dict(self.public)
        p256 = ec.generate_private_key(ec.SECP256R1())
        bad["guardian"] = p256.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with self.assertRaisesRegex(CertificateError, "must be secp256k1"):
            verify_five_party_certificate(self.envelope, self.signatures(), bad, self.store, now=self.now)


if __name__ == "__main__":
    unittest.main()
