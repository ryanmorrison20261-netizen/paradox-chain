# PARADOX Chain — public ledger snapshot

Read-only publication of the PARADOX chain, sealed **2026-10-27**. This is the final
baseline: 3 blocks, hash-linked back to Satoshi Genesis, every block signed by o².

Only public material is in this repository. **No private key is present or has ever been
present here.**

## What is in here

| File | What it is |
|---|---|
| `paradox-chain.jsonl` | The ledger, one JSON block per line (3 blocks) |
| `pin.json` | o²'s pinned public identity and genesis signature |
| `o2_public.pem` | o² public key (secp256k1) |
| `me_rsa_public.pem` | Identity public key (RSA-3072) |
| `index.html` | Viewer page — re-verifies every link and signature in the browser |
| `recovery.html` | Recovery / one-go check page |
| `paradox-chain.jsonl.ots` | OpenTimestamps proof for the chain file |

## Verifying it yourself

Chain file sha256:

```
72e8f7db181ff1337a7a534208c9e60858e95f84644df318af82b3e21b4fd6cd  paradox-chain.jsonl
```

Pinned o² public key:

```
039063f32bfe91c9b8399ce5524c527978ddb58d6f86d30eb821b0ef10aa48d871
```

Tip (block 2):

```
8f7c9936eab1f3c45da60cf9608dfc3e08c9eb331ec30b58256c5ebaef3198e3
```

Sealed at `2026-10-27T14:08:27.455Z` (block 0). The page in `index.html` recomputes every
block hash, checks each `prev` link back to the genesis seal, and verifies each signature
against the pinned key. Each block carries `height`, `time`, `data`, `prev`, `hash`, and a
secp256k1 `sig`.

## What this chain contains

- **Block 0** — the o² genesis seal: `Satoshi Genesis` anchor, o²'s key, and the o² signature.
- **Block 1** — "o² opens the PARADOX chain · MetaParadox is live".
- **Block 2** — the keeper's RSA-3072 identity, verified and recorded.

Note: this revision predates the three-node binding format. `pin.json` here has no `nodes`
map, so a node-binding check reports the seal as pre-restart. That is a property of this
sealed revision, not a fault in the file.

## What this is not

This is a signed, hash-linked ledger published for inspection. It is **not** a blockchain
network: no peers, no mining, no consensus, and **no block rewards**. The name
"Satoshi Genesis" in the genesis seal refers to the Bitcoin mainnet block-0 hash used as a
timestamp anchor constant, not to any coin issuance.

## Anchoring

`paradox-chain.jsonl.ots` is an OpenTimestamps proof bound to the exact digest above,
submitted to `bob.btc.calendar.opentimestamps.org`, `btc.calendar.catallaxy.com` and
`finney.calendar.eternitywall.com`.

Status: **PendingAttestation** — the calendars hold the digest but it is not yet committed
inside a Bitcoin block.

```
curl -O https://raw.githubusercontent.com/ryanmorrison20261-netizen/paradox-chain/main/paradox-chain.jsonl
curl -O https://raw.githubusercontent.com/ryanmorrison20261-netizen/paradox-chain/main/paradox-chain.jsonl.ots
pip install opentimestamps-client
ots upgrade paradox-chain.jsonl.ots
ots verify  paradox-chain.jsonl.ots
```

Once `ots verify` reports a Bitcoin block, the file's existence at or before that block is
proven by Bitcoin's proof-of-work — verifiable by anyone, trusting no server. Do not edit
`paradox-chain.jsonl`: the proof is bound to its exact bytes.

A separate, already-confirmed proof covers an earlier 4-ledger **tipset**
(sha256 `c41ea537…`, Bitcoin block 975093). It anchors different data and does not apply to
this file.

## Superseded revision

A 4-block revision sealed `2026-11-08` (chain sha256 `5c11e845…`, all three nodes bound) was
published here briefly and has been reverted. It remains in this repository's git history
but is **not** the current chain.

## Trust model

The ledger is only as trustworthy as the pinned o² key above. If that pin matches a value
you recorded independently, the chain content is authentic to that key.
