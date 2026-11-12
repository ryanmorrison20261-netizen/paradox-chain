#!/usr/bin/env python3
"""
crosscheck.py — independently cross-check a Bitcoin block header + transaction.

Recomputes everything locally from RAW bytes fetched from two explorers:
  - header hash, proof-of-work vs its bits
  - header chain linkage (N blocks before / after), PoW of each
  - timestamp consensus rule: time > median of previous 11 blocks (MTP)
  - timestamp sanity: within 2h of the next blocks' MTP window, before now
  - difficulty: bits equals the bits of the retarget period's first block
  - merkle root rebuilt from the block's full txid list
  - tx: raw tx hashes to txid, txid is in the block
  - main chain: both explorers return the same hash at that height
Writes report.txt + report.json (with SHA-256 of the report).

Usage: ./crosscheck.py <header_hex_80_bytes> <txid> [--before 11] [--after 6] [--out DIR]
"""
import argparse, hashlib, json, os, struct, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from statistics import median

SRC = {"mempool.space": "https://mempool.space/api", "blockstream.info": "https://blockstream.info/api"}


def get(url, js=False, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "crosscheck/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        b = r.read()
    return b if raw else (json.loads(b) if js else b.decode().strip())


dsha = lambda b: hashlib.sha256(hashlib.sha256(b).digest()).digest()


def parse_header(b):
    v, = struct.unpack("<I", b[0:4]); t, bits, nonce = struct.unpack("<III", b[68:80])
    exp = bits >> 24; tgt = (bits & 0x7fffff) << (8 * (exp - 3)) if exp > 3 else (bits & 0x7fffff) >> (8 * (3 - exp))
    h = dsha(b)[::-1].hex()
    return {"hash": h, "version": v, "prev": b[4:36][::-1].hex(), "merkle_root": b[36:68][::-1].hex(),
            "time": t, "bits": bits, "nonce": nonce, "target": tgt,
            "difficulty": (0xffff << 208) / tgt, "pow_ok": int(h, 16) <= tgt}


def merkle_root(txids_be):
    layer = [bytes.fromhex(t)[::-1] for t in txids_be]
    while len(layer) > 1:
        if len(layer) % 2: layer.append(layer[-1])
        layer = [dsha(layer[i] + layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0][::-1].hex()


def tx_strip_hash(raw):
    """txid of a raw tx (strip segwit marker/flag/witness)."""
    if raw[4:6] != b"\x00\x01":
        return dsha(raw)[::-1].hex()
    p = 6
    def vi():
        nonlocal p
        f = raw[p]; p += 1
        if f < 0xfd: return f
        n = {0xfd: 2, 0xfe: 4, 0xff: 8}[f]; x = int.from_bytes(raw[p:p + n], "little"); p += n; return x
    s = p
    for _ in range(vi()): p += 36; l = vi(); p += l + 4
    for _ in range(vi()): p += 8; l = vi(); p += l
    e = p
    return dsha(raw[:4] + raw[s:e] + raw[-4:])[::-1].hex()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("header_hex"); ap.add_argument("txid")
    ap.add_argument("--before", type=int, default=11); ap.add_argument("--after", type=int, default=6)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    checks, data = [], {}
    def chk(ok, name, detail):
        checks.append({"ok": bool(ok), "check": name, "detail": detail})

    hb = bytes.fromhex(a.header_hex.strip())
    chk(len(hb) == 80, "Header is 80 bytes", f"{len(hb)} bytes")
    H = parse_header(hb); data["header"] = {k: (v if k != "target" else hex(v)) for k, v in H.items()}
    chk(H["pow_ok"], "Header proof-of-work", f"hash {H['hash']} <= target from bits {H['bits']:#x} (difficulty {H['difficulty']:.2f})")

    # --- main chain: same hash at that height on both explorers ---
    try:
        info = {n: get(f"{b}/block/{H['hash']}", js=True) for n, b in SRC.items()}
    except urllib.error.HTTPError as e:
        chk(False, "Block exists on the explorers", f"hash {H['hash']} not found (HTTP {e.code}) — header is altered or not from Bitcoin")
        for c in checks: print(f"[{'PASS' if c['ok'] else 'FAIL'}] {c['check']}\n        {c['detail']}")
        print("\nRESULT: SOME CHECKS FAILED"); return 1
    height = info["mempool.space"]["height"]; data["height"] = height
    at_h = {n: get(f"{b}/block-height/{height}") for n, b in SRC.items()}
    chk(all(v == H["hash"] for v in at_h.values()), "Main chain: both explorers have this hash at its height",
        f"height {height}: " + ", ".join(f"{n}={v[:16]}…" for n, v in at_h.items()))
    for n, b in SRC.items():
        raw = get(f"{b}/block/{H['hash']}/header")
        chk(raw.lower() == a.header_hex.strip().lower(), f"Raw header identical on {n}", raw[:24] + "…")

    # --- header chain linkage + PoW, before and after ---
    base = SRC["mempool.space"]
    hdrs = {}
    for h in range(height - a.before, height + a.after + 1):
        bh = get(f"{base}/block-height/{h}")
        hdrs[h] = parse_header(bytes.fromhex(get(f"{base}/block/{bh}/header")))
        if hdrs[h]["hash"] != bh:
            chk(False, f"Header hash recomputes at {h}", "mismatch")
    link_ok = all(hdrs[h]["prev"] == hdrs[h - 1]["hash"] for h in range(height - a.before + 1, height + a.after + 1))
    pow_ok = all(x["pow_ok"] for x in hdrs.values())
    chk(link_ok, f"Header chain links {height - a.before}..{height + a.after}",
        f"each block's prev-hash equals the recomputed hash of the block before ({len(hdrs)} headers)")
    chk(pow_ok, "Proof-of-work valid on every header in that range", f"{len(hdrs)} headers")

    # --- timestamp rules ---
    prev11 = [hdrs[h]["time"] for h in range(height - 11, height)]
    mtp = int(median(prev11))
    chk(H["time"] > mtp, "Timestamp > median of previous 11 blocks (consensus rule)",
        f"{iso(H['time'])} > MTP {iso(mtp)}")
    later = [hdrs[h]["time"] for h in range(height + 1, height + a.after + 1)]
    chk(H["time"] <= max(later) + 7200, "Timestamp consistent with following blocks (≤ 2h ahead)",
        f"next {a.after} blocks: {iso(min(later))} … {iso(max(later))}")
    chk(H["time"] < datetime.now(timezone.utc).timestamp(), "Timestamp is in the past", iso(H["time"]))
    data["timestamps"] = {str(h): iso(hdrs[h]["time"]) for h in sorted(hdrs)}

    # --- difficulty period ---
    pstart = height - height % 2016
    pb = parse_header(bytes.fromhex(get(f"{base}/block/{get(f'{base}/block-height/{pstart}')}/header")))
    chk(pb["bits"] == H["bits"], "Difficulty bits match the retarget period",
        f"period starts at {pstart}, bits {pb['bits']:#x}")

    # --- merkle root from full txid list ---
    for n, b in SRC.items():
        txids = get(f"{b}/block/{H['hash']}/txids", js=True)
        r = merkle_root(txids)
        chk(r == H["merkle_root"], f"Merkle root rebuilt from {n} txid list", f"{len(txids)} txs -> {r[:16]}…")
    chk(a.txid in txids, "txid is in this block", f"position {txids.index(a.txid) if a.txid in txids else '-'}")

    # --- tx raw bytes ---
    for n, b in SRC.items():
        raw = get(f"{b}/tx/{a.txid}/raw", raw=True)
        chk(tx_strip_hash(raw) == a.txid, f"Raw tx from {n} hashes to txid", f"{len(raw)} bytes")
    tipn = int(get(f"{base}/blocks/tip/height"))
    data["confirmations"] = tipn - height + 1

    # --- report ---
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tip_hash = get(f"{base}/blocks/tip/hash")
    report = {"checked_at": now, "anchor_tip": {"height": tipn, "hash": tip_hash},
              "txid": a.txid, "block": H["hash"], "height": height,
              "all_passed": all(c["ok"] for c in checks), "checks": checks, "data": data}
    os.makedirs(a.out, exist_ok=True)
    jp = os.path.join(a.out, "crosscheck_report.json")
    with open(jp, "w") as f: json.dump(report, f, indent=2)
    digest = hashlib.sha256(open(jp, "rb").read()).hexdigest()
    lines = [f"CROSS-CHECK REPORT  {now}", f"txid   {a.txid}", f"block  {H['hash']}  (height {height}, {iso(H['time'])})",
             f"confirmations {data['confirmations']:,}  (tip {tipn} {tip_hash})", ""]
    lines += [f"[{'PASS' if c['ok'] else 'FAIL'}] {c['check']}\n        {c['detail']}" for c in checks]
    lines += ["", f"RESULT: {'ALL CHECKS PASSED' if report['all_passed'] else 'SOME CHECKS FAILED'}",
              f"report.json sha256: {digest}"]
    txt = "\n".join(lines); open(os.path.join(a.out, "crosscheck_report.txt"), "w").write(txt + "\n")
    print(txt)
    return 0 if report["all_passed"] else 1


def iso(t): return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


if __name__ == "__main__":
    sys.exit(main())
