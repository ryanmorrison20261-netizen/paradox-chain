#!/usr/bin/env python3
"""
chainverify.py — verify the ENTIRE Bitcoin header chain locally, in one pass.

Input: raw 80-byte headers, concatenated in height order (e.g. block-dn.org/headers/<start>
files, 100,000 headers each). The download source is NOT trusted: every rule is re-checked.

Rules checked for every block:
  1. genesis hash equals the hard-coded Bitcoin genesis hash
  2. prev-hash links to the recomputed hash of the previous header
  3. proof-of-work: hash <= target encoded in bits
  4. difficulty: bits unchanged inside a 2016-block period; at each retarget the
     new bits equal Bitcoin Core's exact formula (timespan clamp x4, pow limit)
  5. timestamp: > median time of the previous 11 blocks (consensus MTP rule)
  6. version: >=2 / >=3 / >=4 after BIP34 / BIP66 / BIP65 activation heights
Outputs checkpoints.json: hash + cumulative work at every retarget boundary and the tip.

Usage: ./chainverify.py h_0.bin h_100000.bin ... [--out checkpoints.json] [--check H:HASH ...]
"""
import argparse, hashlib, json, sys, time
from datetime import datetime, timezone

GENESIS = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
POW_LIMIT = 0x00000000FFFF << 208
SPAN = 14 * 24 * 60 * 60
VERSION_RULES = [(388381, 4), (363725, 3), (227931, 2)]  # BIP65, BIP66, BIP34 mainnet heights


def set_compact(c):
    size, word = c >> 24, c & 0x007FFFFF
    return word >> 8 * (3 - size) if size <= 3 else word << 8 * (size - 3)


def get_compact(n):
    size = (n.bit_length() + 7) // 8
    compact = n << 8 * (3 - size) if size <= 3 else n >> 8 * (size - 3)
    if compact & 0x00800000:
        compact >>= 8; size += 1
    return compact | size << 24


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="checkpoints.json")
    ap.add_argument("--check", nargs="*", default=[], help="HEIGHT:HASH pairs to confirm")
    a = ap.parse_args()

    t0 = time.time()
    data = b"".join(open(f, "rb").read() for f in a.files)
    if len(data) % 80:
        sys.exit(f"ERROR: {len(data)} bytes is not a multiple of 80")
    n = len(data) // 80
    sha = hashlib.sha256
    fb = int.from_bytes
    times = [0] * n
    hashes = [None] * n
    errors, checkpoints = [], []
    work = 0
    prev_hash_le = None
    bits_prev = None

    def err(h, msg):
        if len(errors) < 50: errors.append(f"height {h}: {msg}")

    for h in range(n):
        hd = data[h * 80:(h + 1) * 80]
        hl = sha(sha(hd).digest()).digest()          # hash, little-endian
        hashes[h] = hl
        ver = fb(hd[0:4], "little")
        t = fb(hd[68:72], "little"); times[h] = t
        bits = fb(hd[72:76], "little")
        target = set_compact(bits)

        if h == 0:
            if hl[::-1].hex() != GENESIS: err(0, "genesis hash mismatch")
        elif hd[4:36] != prev_hash_le:
            err(h, "prev-hash does not link")

        if fb(hl, "little") > target or target == 0 or target > POW_LIMIT:
            err(h, "proof-of-work fails")

        if h > 0:
            if h % 2016 == 0:
                actual = times[h - 1] - times[h - 2016]
                actual = min(max(actual, SPAN // 4), SPAN * 4)
                new = set_compact(bits_prev) * actual // SPAN
                expect = get_compact(min(new, POW_LIMIT))
                if bits != expect: err(h, f"retarget bits {bits:#x} != expected {expect:#x}")
            elif bits != bits_prev:
                err(h, "bits changed mid-period")
            win = sorted(times[max(0, h - 11):h])
            if t <= win[len(win) // 2]:
                err(h, "timestamp not above median of previous 11")

        for act, minv in VERSION_RULES:
            if h >= act:
                if ver < minv: err(h, f"version {ver} < {minv}")
                break

        work += (1 << 256) // (target + 1)
        if h % 2016 == 0 or h == n - 1:
            checkpoints.append({"height": h, "hash": hl[::-1].hex(), "time": t, "chainwork": hex(work)})
        prev_hash_le = hl
        bits_prev = bits

    secs = time.time() - t0
    checked = []
    for c in a.check:
        hh, hx = c.split(":")
        hh = int(hh)
        got = hashes[hh][::-1].hex() if hh < n else None
        checked.append({"height": hh, "expected": hx, "got": got, "match": got == hx})

    out = {
        "format": "chain-checkpoints-v1",
        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "headers": n, "tip_height": n - 1, "tip_hash": hashes[-1][::-1].hex(),
        "chainwork": hex(work), "all_rules_passed": not errors,
        "rules": ["genesis", "linkage", "proof-of-work", "difficulty retarget (exact)",
                  "median-time-past", "BIP34/65/66 versions"],
        "interval": 2016, "checkpoints": checkpoints,
    }
    json.dump(out, open(a.out, "w"))

    print(f"headers verified : {n:,}  (heights 0..{n - 1:,})")
    print(f"time             : {secs:.1f} s  ({n / secs:,.0f} headers/s)")
    print(f"genesis          : {GENESIS}")
    print(f"tip              : {n - 1}  {out['tip_hash']}")
    print(f"total chainwork  : {work:#x}  (~2^{work.bit_length() - 1})")
    print(f"checkpoints      : {len(checkpoints)} written to {a.out}")
    for c in checked:
        print(f"check {c['height']:>7}: {'MATCH' if c['match'] else 'MISMATCH'}  {c['got']}")
    print(f"\nRESULT: {'ALL RULES PASSED FOR EVERY BLOCK' if not errors else 'ERRORS FOUND'}")
    for e in errors: print("  " + e)
    return 0 if not errors and all(c["match"] for c in checked) else 1


if __name__ == "__main__":
    sys.exit(main())
