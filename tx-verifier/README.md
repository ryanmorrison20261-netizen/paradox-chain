# Bitcoin Tx Auto-Verifier

Live page: https://ryanmorrison20261-netizen.github.io/paradox-chain/tx-verifier/
(link straight to a tx: `.../tx-verifier/?tx=<txid>`)

Type a txid (or an address to pick one of its transactions). In your browser it:

1. pulls raw tx + status from mempool.space **and** blockstream.info and requires them to match
2. verifies with Bitcoin's own math: txid hash, merkle inclusion, block proof-of-work
3. links the block by PoW-checked headers to `checkpoints.json` — produced by `tools/chainverify.py`,
   which verified **every** header from genesis (PoW, links, exact retargets, MTP timestamps, versions)
4. checks the block timestamp against the median of the previous 11 blocks
5. shows the money flow: where each input started, where each output ended (tap to follow)
6. writes a report with a hash-chained, timestamped audit trail of every step
7. timestamps the report's SHA-256 with OpenTimestamps (`ots upgrade` / `ots verify` later)
8. multisig: ECDSA P-256 signatures from PEM keys, valid only at the `signers.json` threshold

Offline mode: import a bundle from `tools/txcheck.py <txid> --bundle b.json` — no network used.

## Tools (macOS: `chmod +x tools/*.py`)
| script | does |
|---|---|
| `txcheck.py <txid> [--bundle f.json]` | live 2-explorer check; bundle for offline proof |
| `chainverify.py h_*.bin` | verify the whole header chain (headers: block-dn.org/headers/0 … /900000) |
| `crosscheck.py <header_hex> <txid>` | deep cross-check of one block + tx |
| `reportsign.py keygen/sign/verify` | M-of-N multisig with PEM keys; checks the audit trail |

**`signers.json` holds DEMO keys.** Replace it with your own:
`tools/reportsign.py keygen --names a b c --threshold 2` → keep `keys/*.pem` offline, publish `signers.json`.

Explorer data still trusted: the tip height used for the confirmation count. Fully trustless = your own node.
