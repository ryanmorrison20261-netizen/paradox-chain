#!/usr/bin/env python3
"""
reportsign.py — M-of-N multisig signing for txproof reports with PEM keys.
ECDSA P-256 / SHA-256 over the exact report bytes; signatures stored as raw r||s (base64),
the same format the Auto-Verifier page produces and checks.

  ./reportsign.py keygen --names alice bob carol --threshold 2 --dir keys
        -> keys/<name>.pem (PRIVATE, chmod 600), keys/<name>.pub.pem, signers.json
  ./reportsign.py sign report.json keys/alice.pem keys/bob.pem [--signers signers.json] [--out report.sigs.json]
  ./reportsign.py verify report.json report.sigs.json [--signers signers.json]
        exit 0 = threshold met, 1 = not met
"""
import argparse, base64, hashlib, json, os, sys
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature
from cryptography.exceptions import InvalidSignature


def pub_pem(pub):
    return pub.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()


norm = lambda p: "".join(p.split())


def keygen(a):
    os.makedirs(a.dir, exist_ok=True)
    signers = []
    for n in a.names:
        k = ec.generate_private_key(ec.SECP256R1())
        p = os.path.join(a.dir, f"{n}.pem")
        with open(p, "wb") as f:
            f.write(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        os.chmod(p, 0o600)
        open(os.path.join(a.dir, f"{n}.pub.pem"), "w").write(pub_pem(k.public_key()))
        signers.append({"name": n, "pubkey_pem": pub_pem(k.public_key())})
    json.dump({"threshold": a.threshold, "signers": signers}, open(a.signers, "w"), indent=2)
    print(f"generated {len(signers)} keys in {a.dir}/ (private .pem are chmod 600 — keep them offline)")
    print(f"wrote {a.signers}: {a.threshold}-of-{len(signers)} — publish this file next to the page")


def load_signers(path):
    return json.load(open(path)) if path and os.path.exists(path) else None


def sign(a):
    data = open(a.report, "rb").read()
    S = load_signers(a.signers)
    sigs = []
    for kp in a.keys:
        k = serialization.load_pem_private_key(open(kp, "rb").read(), password=None)
        if not isinstance(k, ec.EllipticCurvePrivateKey) or k.curve.name != "secp256r1":
            sys.exit(f"{kp}: not a P-256 key")
        r, s = decode_dss_signature(k.sign(data, ec.ECDSA(hashes.SHA256())))
        pp = pub_pem(k.public_key())
        name = next((x["name"] for x in (S or {}).get("signers", []) if norm(x["pubkey_pem"]) == norm(pp)), os.path.basename(kp).rsplit(".", 1)[0])
        sigs.append({"signer": name, "alg": "ES256", "pubkey_pem": pp,
                     "sig_b64": base64.b64encode(r.to_bytes(32, "big") + s.to_bytes(32, "big")).decode()})
    out = {"format": "txproof-sigs-v1", "report_sha256": hashlib.sha256(data).hexdigest(),
           "threshold": (S or {}).get("threshold", len(sigs)), "signatures": sigs}
    json.dump(out, open(a.out, "w"), indent=2)
    print(f"signed {a.report} with {len(sigs)} key(s) -> {a.out}")


def verify(a):
    data = open(a.report, "rb").read()
    sg = json.load(open(a.sigs))
    S = load_signers(a.signers)
    need = S["threshold"] if S else 1
    ok_count, seen = 0, set()
    h = hashlib.sha256(data).hexdigest()
    hash_ok = sg.get("report_sha256") in (None, h)
    print(f"report sha256 {h} {'(matches signature file)' if hash_ok else '(DOES NOT MATCH signature file)'}")
    for s in sg.get("signatures", []):
        valid = False
        try:
            pub = serialization.load_pem_public_key(s["pubkey_pem"].encode())
            raw = base64.b64decode(s["sig_b64"])
            pub.verify(encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")), data, ec.ECDSA(hashes.SHA256()))
            valid = True
        except (InvalidSignature, ValueError, KeyError):
            pass
        trusted = next((x["name"] for x in (S or {}).get("signers", []) if norm(x["pubkey_pem"]) == norm(s["pubkey_pem"])), None)
        dup = norm(s["pubkey_pem"]) in seen
        seen.add(norm(s["pubkey_pem"]))
        good = valid and trusted and not dup
        ok_count += bool(good)
        print(f"  [{'PASS' if good else 'FAIL'}] {s.get('signer')}: signature {'valid' if valid else 'INVALID'}"
              f"{', trusted key ' + repr(trusted) if trusted else ', key NOT trusted'}{', duplicate' if dup else ''}")
    trail_ok = check_trail(data)
    met = hash_ok and ok_count >= need and trail_ok is not False
    print(f"\nMULTISIG {'VALID' if met else 'NOT MET'}: {ok_count} of {len(S['signers']) if S else '?'} trusted signers (need {need})")
    return 0 if met else 1


def check_trail(data):
    """Recompute the report's hash-chained audit trail. None = report has no trail."""
    try:
        tr = json.loads(data).get("audit_trail")
    except ValueError:
        return None
    if not tr:
        return None
    prev = tr.get("genesis", "0" * 64)
    for i, s in enumerate(tr["steps"]):
        h = hashlib.sha256(f"{prev}|{s['t']}|{s['state']}|{s['msg']}".encode()).hexdigest()
        if s["prev"] != prev or s["hash"] != h:
            print(f"  [FAIL] audit trail broken at step {i + 1}: {s['msg'][:60]}")
            return False
        prev = h
    ok = prev == tr["head"]
    steps = tr["steps"]
    print(f"  [{'PASS' if ok else 'FAIL'}] audit trail: {len(steps)} timestamped steps, {steps[0]['t']} -> {steps[-1]['t']}, chain intact, head {prev[:16]}…")
    return ok


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("keygen"); g.add_argument("--names", nargs="+", required=True); g.add_argument("--threshold", type=int, required=True)
    g.add_argument("--dir", default="keys"); g.add_argument("--signers", default="signers.json")
    s = sp.add_parser("sign"); s.add_argument("report"); s.add_argument("keys", nargs="+"); s.add_argument("--signers", default="signers.json"); s.add_argument("--out", default="report.sigs.json")
    v = sp.add_parser("verify"); v.add_argument("report"); v.add_argument("sigs"); v.add_argument("--signers", default="signers.json")
    a = ap.parse_args()
    return {"keygen": keygen, "sign": sign, "verify": verify}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
