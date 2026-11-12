#!/usr/bin/env python3
"""
txcheck — verify a Bitcoin transaction is confirmed, using two independent
public explorers (mempool.space and blockstream.info). No API keys, stdlib only.

Usage:
  ./txcheck.py <txid> [<txid> ...] [--address ADDR] [--amount BTC] [--min-conf N] [--json]
  ./txcheck.py <txid> [<txid> ...] --bundle proof.json   # also save a bundle for the
                                                         # Bitcoin Tx Proof Verifier artifact

Exit codes:
  0  VERIFIED   (confirmed with >= min-conf on both sources, and expected output matches if given)
  1  NOT VERIFIED (unconfirmed, too few confirmations, sources disagree, or output mismatch)
  2  ERROR      (bad txid, tx not found, or network failure on every source)
"""
import argparse, json, os, re, sys, urllib.request, urllib.error
from datetime import datetime, timezone

SOURCES = {
    "mempool.space": "https://mempool.space/api",
    "blockstream.info": "https://blockstream.info/api",
}
TIMEOUT = 15


def get(url, as_json=True):
    req = urllib.request.Request(url, headers={"User-Agent": "txcheck/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = r.read().decode()
    return json.loads(body) if as_json else body.strip()


def query(name, base, txid):
    """Return dict for one source, or {'error': ...}."""
    try:
        tx = get(f"{base}/tx/{txid}")
        tip = int(get(f"{base}/blocks/tip/height", as_json=False))
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return {"source": name, "error": "transaction not found"}
        return {"source": name, "error": f"HTTP {e.code}"}
    except Exception as e:  # network, timeout, bad JSON
        return {"source": name, "error": str(e)}
    st = tx.get("status", {})
    confirmed = bool(st.get("confirmed"))
    height = st.get("block_height")
    confs = (tip - height + 1) if confirmed and height is not None else 0
    outs = [
        {"address": o.get("scriptpubkey_address", "(non-address output)"),
         "btc": o.get("value", 0) / 1e8}
        for o in tx.get("vout", [])
    ]
    return {
        "source": name,
        "confirmed": confirmed,
        "block_height": height,
        "block_hash": st.get("block_hash"),
        "block_time": st.get("block_time"),
        "tip_height": tip,
        "confirmations": confs,
        "fee_btc": tx.get("fee", 0) / 1e8,
        "outputs": outs,
    }


HEADERS_URL = "https://block-dn.org/headers/{start}"   # 100,000 raw headers per file
HEADERS_CACHE = os.path.expanduser("~/.cache/txcheck")


def headers_range(lo, hi):
    """Raw 80-byte headers for heights lo..hi inclusive (cached per 100k file).
    Source is untrusted: the verifier re-checks linkage + PoW against checkpoints."""
    os.makedirs(HEADERS_CACHE, exist_ok=True)
    out = b""
    for start in range(lo // 100000 * 100000, hi + 1, 100000):
        path = os.path.join(HEADERS_CACHE, f"h_{start}.bin")
        need_end = min(hi, start + 99999)
        if not os.path.exists(path) or os.path.getsize(path) < (need_end - start + 1) * 80:
            req = urllib.request.Request(HEADERS_URL.format(start=start), headers={"User-Agent": "txcheck/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                f.write(r.read())
        blob = open(path, "rb").read()
        a, b = max(lo, start) - start, need_end - start + 1
        out += blob[a * 80:b * 80]
    if len(out) != (hi - lo + 1) * 80:
        raise ValueError("header source does not reach that height yet")
    return out


def fetch_bundle_entry(txid, cp_height=None):
    """Raw data the proof-verifier page checks itself (tx hex, merkleblock proof) plus
    explorer data (status, tip). Tries each source until one returns everything."""
    errs = []
    for name, base in SOURCES.items():
        try:
            e = {
                "txid": txid,
                "tx_hex": get(f"{base}/tx/{txid}/hex", as_json=False),
                "merkleblock_hex": get(f"{base}/tx/{txid}/merkleblock-proof", as_json=False),
                "status": get(f"{base}/tx/{txid}/status"),
                "tip_height": int(get(f"{base}/blocks/tip/height", as_json=False)),
                "source": name,
            }
            break
        except Exception as ex:  # unconfirmed tx has no merkle proof -> 400/404
            errs.append(f"{name}: {ex}")
    else:
        return {"txid": txid, "error": "; ".join(errs)}
    # block reward data: coinbase tx + its merkle proof (verified by the page), fees (explorer)
    bh = e["status"].get("block_hash")
    if bh:
        try:
            base = SOURCES[e["source"]]
            cbid = get(f"{base}/block/{bh}/txid/0", as_json=False)
            e["reward"] = {
                "coinbase_txid": cbid,
                "coinbase_hex": get(f"{base}/tx/{cbid}/hex", as_json=False),
                "coinbase_merkleblock_hex": get(f"{base}/tx/{cbid}/merkleblock-proof", as_json=False),
                "tx_fee_sats": get(f"{base}/tx/{txid}").get("fee"),
            }
            try:
                e["reward"]["total_fees_sats"] = get(f"https://mempool.space/api/v1/block/{bh}")["extras"]["totalFees"]
            except Exception:
                pass
        except Exception as ex:
            e["reward_error"] = str(ex)
    # headers from the block up to the next 2016-block checkpoint (main-chain proof)
    h = e["status"].get("block_height")
    if h is not None:
        cp = -(-h // 2016) * 2016
        if cp_height is not None and cp > cp_height:
            cp = cp_height if cp_height >= h else None
        try:
            if cp is not None and cp > h:
                e["chain_headers_hex"] = headers_range(h + 1, cp).hex()
            e["chain_to_height"] = cp
        except Exception as ex:
            e["chain_error"] = str(ex)
    return e


def main():
    p = argparse.ArgumentParser(description="Verify a Bitcoin tx is confirmed (2 explorers).")
    p.add_argument("txids", nargs="+", metavar="txid")
    p.add_argument("--bundle", metavar="FILE", help="also write a proof bundle JSON for the verifier artifact")
    p.add_argument("--checkpoints", metavar="FILE", help="checkpoints.json from chainverify.py (caps chain proof at its tip)")
    p.add_argument("--address", help="expected receiving address")
    p.add_argument("--amount", type=float, help="expected BTC to that address (needs --address)")
    p.add_argument("--min-conf", type=int, default=3, help="confirmations required (default 3)")
    p.add_argument("--json", action="store_true", help="print machine-readable JSON")
    a = p.parse_args()
    codes, entries = [], []
    for i, t in enumerate(a.txids):
        if i:
            print("\n" + "-" * 60)
        codes.append(check_one(t, a))
        txid = t.strip().lower()
        if a.bundle and re.fullmatch(r"[0-9a-f]{64}", txid):
            cph = json.load(open(a.checkpoints))["tip_height"] if a.checkpoints else None
            entries.append(fetch_bundle_entry(txid, cph))
    if a.bundle:
        bundle = {"format": "txproof-bundle-v1",
                  "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "entries": entries}
        with open(a.bundle, "w") as f:
            json.dump(bundle, f)
        good = sum(1 for e in entries if "error" not in e)
        print(f"\nbundle: wrote {a.bundle} ({good}/{len(entries)} tx with proofs)", file=sys.stderr)
        for e in entries:
            if "error" in e:
                print(f"  no proof for {e['txid']}: {e['error']}", file=sys.stderr)
    return max(codes)


def check_one(txid_in, a):
    txid = txid_in.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", txid):
        print(f"ERROR: txid must be 64 hex characters: {txid_in}", file=sys.stderr)
        return 2

    results = [query(n, b, txid) for n, b in SOURCES.items()]
    ok = [r for r in results if "error" not in r]
    problems = []

    if not ok:
        verdict, code = "ERROR", 2
        problems.append("no source could return this transaction")
    else:
        if len(ok) < len(results):
            problems.append("only one source answered — not independently confirmed")
        if len({(r["confirmed"], r["block_hash"]) for r in ok}) > 1:
            problems.append("sources DISAGREE on confirmation/block")
        confs = min(r["confirmations"] for r in ok)
        if not all(r["confirmed"] for r in ok):
            problems.append("UNCONFIRMED (in mempool) — can still be replaced or dropped")
        elif confs < a.min_conf:
            problems.append(f"only {confs} confirmation(s), need {a.min_conf}")

        match = None
        if a.address:
            paid = sum(o["btc"] for o in ok[0]["outputs"] if o["address"] == a.address)
            match = {"address": a.address, "paid_btc": round(paid, 8)}
            if paid == 0:
                problems.append(f"no output pays {a.address}")
            elif a.amount is not None and round(paid, 8) < round(a.amount, 8):
                problems.append(f"{a.address} received {paid:.8f} BTC, expected {a.amount:.8f}")

        verdict, code = ("VERIFIED", 0) if not problems else ("NOT VERIFIED", 1)

    report = {
        "txid": txid,
        "verdict": verdict,
        "min_conf": a.min_conf,
        "problems": problems,
        "sources": results,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if a.address:
        report["expected_output"] = match if ok else None

    if a.json:
        print(json.dumps(report, indent=2))
        return code

    print(f"txid: {txid}")
    for r in results:
        if "error" in r:
            print(f"  [{r['source']}] ERROR: {r['error']}")
            continue
        when = (datetime.fromtimestamp(r["block_time"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                if r["block_time"] else "-")
        state = f"confirmed, block {r['block_height']} ({when}), {r['confirmations']} conf" \
            if r["confirmed"] else "UNCONFIRMED"
        print(f"  [{r['source']}] {state}")
    if ok:
        print(f"  fee: {ok[0]['fee_btc']:.8f} BTC")
        print("  outputs:")
        for o in ok[0]["outputs"]:
            mark = "  <-- expected" if a.address and o["address"] == a.address else ""
            print(f"    {o['btc']:.8f} BTC  {o['address']}{mark}")
    print(f"\nVERDICT: {verdict}")
    for pr in problems:
        print(f"  - {pr}")
    return code


if __name__ == "__main__":
    sys.exit(main())
