import unittest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from der_multiauth import AuthError, NonceStore, RequestEnvelope, load_secp256k1_public_key, verify_der_signature, verify_threshold

class DERMultiAuthTests(unittest.TestCase):
    def setUp(self):
        self.keys = {n: ec.generate_private_key(ec.SECP256K1()) for n in ("alice", "bob", "carol")}
        self.pubs = {n: k.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo) for n, k in self.keys.items()}
        self.now = 1700000000
        self.envelope = RequestEnvelope("POST", "/v1/proof", self.now, "nonce-000000000001", b'{"amount":1}')

    def signatures(self, names, envelope=None):
        e = envelope or self.envelope
        return {n: self.keys[n].sign(e.message(), ec.ECDSA(hashes.SHA256())) for n in names}

    def test_valid_2_of_3(self):
        self.assertTrue(verify_threshold(self.envelope, self.signatures(("alice", "bob")), self.pubs, 2, NonceStore(), now=self.now)[0])

    def test_below_threshold(self):
        self.assertFalse(verify_threshold(self.envelope, self.signatures(("alice",)), self.pubs, 2, NonceStore(), now=self.now)[0])

    def test_tampered_body(self):
        altered = RequestEnvelope("POST", "/v1/proof", self.now, "nonce-000000000002", b'{"amount":999}')
        self.assertFalse(verify_threshold(altered, self.signatures(("alice", "bob")), self.pubs, 2, NonceStore(), now=self.now)[0])

    def test_untrusted_signer(self):
        with self.assertRaises(AuthError):
            verify_threshold(self.envelope, {"intruder": b"bad"}, self.pubs, 1, NonceStore(), now=self.now)

    def test_replay_rejected(self):
        store = NonceStore()
        sigs = self.signatures(("alice",))
        self.assertTrue(verify_threshold(self.envelope, sigs, self.pubs, 1, store, now=self.now)[0])
        with self.assertRaises(AuthError):
            verify_threshold(self.envelope, sigs, self.pubs, 1, store, now=self.now)

    def test_expired_timestamp(self):
        with self.assertRaises(AuthError):
            verify_threshold(self.envelope, self.signatures(("alice", "bob")), self.pubs, 2, NonceStore(), now=self.now + 301)

    def test_bad_der(self):
        self.assertFalse(verify_der_signature(self.keys["alice"].public_key(), self.envelope.message(), b"\\x30\\x00"))

    def test_wrong_curve_rejected(self):
        key = ec.generate_private_key(ec.SECP256R1())
        pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        with self.assertRaises(AuthError):
            load_secp256k1_public_key(pem)

    def test_duplicate_signature_not_double_counted(self):
        duplicate_pubs = dict(self.pubs)
        duplicate_pubs["alice-copy"] = self.pubs["alice"]
        sigs = {"alice": self.signatures(("alice",))["alice"]}
        with self.assertRaises(AuthError):
            verify_threshold(self.envelope, sigs, duplicate_pubs, 2, NonceStore(), now=self.now)

    def test_signature_for_other_request_rejected(self):
        other = RequestEnvelope("GET", "/v1/other", self.now, "nonce-000000000003", b"")
        self.assertFalse(verify_threshold(other, self.signatures(("alice", "bob")), self.pubs, 2, NonceStore(), now=self.now)[0])

    def test_failed_threshold_does_not_consume_nonce(self):
        store = NonceStore()
        self.assertFalse(verify_threshold(self.envelope, self.signatures(("alice",)), self.pubs, 2, store, now=self.now)[0])
        self.assertTrue(verify_threshold(self.envelope, self.signatures(("alice", "bob")), self.pubs, 2, store, now=self.now)[0])

if __name__ == "__main__":
    unittest.main()
