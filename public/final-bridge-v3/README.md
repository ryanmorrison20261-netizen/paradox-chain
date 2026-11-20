# PARADOX Final Bridge v3 — verified local development

Created 2026-11-20. A new, separate Python 3 read-only bridge release integrates three **public mainnet API observations**: Bitcoin tip height via mempool.space, Liquid tip height via blockstream.info, and Lightning network statistics via mempool.space. No transaction signing, wallet control, or direct peer connections.

**Executed local tests:** 7/7 PASS (synthetic endpoint payloads, SHA-256 response hashing, malformed data PENDING, offline PENDING, unknown endpoint rejection, testnet URL rejection, Guardian metadata). Default invocation prints `GUARDIAN=DENY LIVE_FETCH=PENDING`. The tests do not prove that any endpoint was reachable over the internet.

**Release SHA-256:** `56eab407527c718dd653aef421c0627bfc780a27aced507b932a5d0184f72451`. ZIP available in the accompanying ChatGPT conversation. Run `python3 -m unittest -v test_bridge.py`; run `python3 bridge.py --live` to opt into read-only public mainnet observations. Results are UTC-stamped and saved as new receipt files.

**Still PENDING:** live API retrieval, independent full-node validation, Lightning peer connectivity, OCEAN/Telegram/Tor integrations, node deployment, and asset ownership verification. Guardian default-deny and no-testnet policy remain intact. Original Bitcoin signatures and earlier releases were not modified.
