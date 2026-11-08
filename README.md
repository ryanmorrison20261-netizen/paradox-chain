# PARADOX Chain — public ledger snapshot

Read-only publication of the PARADOX chain sealed on **2026-11-08**.

This is a **new chain, built from genesis**: a fresh o² genesis seal, a fresh
secp256k1 node-1 key, a fresh RSA-3072 node-2 identity, and blocks 0-3 recording all of it.

Only public material is in this repository. **No private key is present or has ever been
present here** — both private keys are held locally in the Paradox cipher (scrypt +
AES-256-GCM) and were never exported.

## What is in here

| File | What it is |
|---|---|
| `paradox-chain.jsonl` | The ledger, one JSON block per line (4 blocks) |
| `pin.json` | o²'s pinned public identity, genesis signature, and both node bindings |
| `o2_public.pem` | Node 1 public key (secp256k1) |
| `me_rsa_public.pem` | Node 2 identity public key (RSA-3072) |
| `index.html` | Viewer page — re-verifies every link and signature in the browser |
| `recovery.html` | Recovery / one-go check page |
| `paradox-chain.jsonl.ots` | OpenTimestamps proof for the chain file |

## Verifying it yourself

Chain file sha256:

```
5c11e8457454d093b805e57355f297cd5fa669beab39ddb9c40178e45a2e4443  paradox-chain.jsonl
```

Pinned o² public key (node 1):

```
03b9ebfc410c5a7ed85541a2001af744ee8019a7322a13c1082237c71b65adb0c9
```

Tip (block 3):

```
96f82d8d7351aede5c61f8170d747a48df21607cf27f3fabe793e1df3a74a226
```

Sealed at `2026-11-08T23:45:11.779Z`.

The page in `index.html` recomputes every block hash, checks each `prev` link back to the
genesis seal, and verifies each signature against the pinned key. Every block carries
`height`, `time`, `data`, `prev`, `hash`, and a secp256k1 `sig`.

## Node bindings

This chain records all three nodes, which the previous revision could not:

- **Node 1** — o²'s own secp256k1 key, named inside the genesis seal and recorded in block 1.
- **Node 2** — the keeper's RSA-3072 fingerprint, named inside the seal and recorded in block 2,
  with a signed identity proof anchored to block 2 and recorded as block 3.
- **Node 3** — the chain itself: every block hash-linked back to Satoshi Genesis, all signed by o².

## What this is not

This is a signed, hash-linked ledger published for inspection. It is **not** a blockchain
network: there are no peers, no mining, no consensus, and **no block rewards**. The name
"Satoshi Genesis" in the genesis seal refers to the Bitcoin mainnet block-0 hash used as an
anchor constant, not to any coin issuance.

## Anchoring

`paradox-chain.jsonl.ots` is an OpenTimestamps proof for this exact file, submitted to three
public calendars: `bob.btc.calendar.opentimestamps.org`, `btc.calendar.catallaxy.com`,
`finney.calendar.eternitywall.com`.

Status: **PendingAttestation** — the calendars hold the digest but it is not yet committed
inside a Bitcoin block. Confirmation normally takes a few hours.

```
curl -O https://raw.githubusercontent.com/ryanmorrison20261-netizen/paradox-chain/main/paradox-chain.jsonl
curl -O https://raw.githubusercontent.com/ryanmorrison20261-netizen/paradox-chain/main/paradox-chain.jsonl.ots
pip install opentimestamps-client
ots upgrade paradox-chain.jsonl.ots
ots verify  paradox-chain.jsonl.ots
```

Once `ots verify` reports a Bitcoin block, the file's existence at or before that block is
proven by Bitcoin's proof-of-work — verifiable by anyone, trusting no server.

## Superseded revision

An earlier snapshot (sealed `2026-10-27`, 3 blocks, chain sha256 `72e8f7db…`) was published
here previously. It is preserved in this repository's git history but is **no longer the
current chain** and its node bindings were incomplete.

## Trust model

The ledger is only as trustworthy as the pinned o² key above. If that pin matches a value you
recorded independently, the chain content is authentic to that key.
