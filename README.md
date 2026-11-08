# PARADOX Chain — public ledger snapshot

Read-only publication of the PARADOX chain as it was sealed on **2026-10-27**.

This repository contains only public material: the ledger, the pin, the two public keys
and the viewer page. **No private key is present or has ever been present here.**

## What is in here

| File | What it is |
|---|---|
| `paradox-chain.jsonl` | The ledger, one JSON block per line |
| `pin.json` | o²'s pinned public identity and genesis signature |
| `o2_public.pem` | o² public key (secp256k1) |
| `me_rsa_public.pem` | Identity public key (RSA-3072) |
| `index.html` | Viewer page — re-verifies every link and signature in the browser |
| `recovery.html` | Recovery / one-go check page |

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

The page in `index.html` recomputes every block hash, checks each `prev` link back to the
genesis seal, and verifies each signature against the pinned key. If any of that fails, the
page says so. You can also do it by hand: each block carries `height`, `time`, `data`,
`prev`, `hash`, and a secp256k1 `sig`.

## What this is not

This is a signed, hash-linked ledger published for inspection. It is **not** a blockchain
network: there are no peers, no mining, no consensus, and no block rewards. The name
"Satoshi Genesis" in the genesis seal refers to the Bitcoin mainnet block-0 hash used as a
timestamp anchor, not to any coin issuance.

## Anchoring

`paradox-chain.jsonl.ots` is an OpenTimestamps proof for this exact file
(sha256 `72e8f7db181ff1337a7a534208c9e60858e95f84644df318af82b3e21b4fd6cd`), submitted to
three public calendar servers: `bob.btc.calendar.opentimestamps.org`,
`btc.calendar.catallaxy.com` and `finney.calendar.eternitywall.com`.

Status at publication: **PendingAttestation** — the calendars have accepted the digest but
it is not yet committed inside a Bitcoin block. Confirmation normally takes a few hours.

To check it yourself once it confirms:

```
curl -O https://raw.githubusercontent.com/ryanmorrison20261-netizen/paradox-chain/main/paradox-chain.jsonl
curl -O https://raw.githubusercontent.com/ryanmorrison20261-netizen/paradox-chain/main/paradox-chain.jsonl.ots
pip install opentimestamps-client
ots upgrade paradox-chain.jsonl.ots   # fetches the Bitcoin attestation
ots verify  paradox-chain.jsonl.ots   # prints the block height and merkle path
```

Once `ots verify` reports a Bitcoin block, the file's existence at or before that block's
timestamp is proven by Bitcoin's proof-of-work — verifiable by anyone, without trusting
this repository or any server.

Earlier OTS proofs in the project cover a different (4-block) revision and do not apply to
this file.

## Trust model

The ledger is only as trustworthy as the pinned o² key above. If that pin matches a value
you recorded independently, the chain content is authentic to that key. Republishing the
file elsewhere does not strengthen or weaken it.
