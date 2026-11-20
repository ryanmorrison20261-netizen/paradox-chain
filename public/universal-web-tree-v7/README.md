# PARADOX ONE — Universal Web Tree and Foundations v7

Date: 2026-11-20. This is a versioned architectural foundation, not a deployed crawler, ownership claim, or live global network.

## Root model

One evidence graph with typed nodes and typed directed edges. Every node has id, type, label, provenance, observation_utc, optional source_url, optional content_sha256, and status (VERIFIED, ASSOCIATED, UNVERIFIED, PENDING). Every edge has source, target, relation, evidence_ids, observer, observed_utc, confidence_basis, and authorization_scope. Reject unproven VERIFIED edges. Keep immutable original evidence separate from derived claims.

## Foundational branches

1. Web: domains, DNS, certificates, CT logs, hosting, APIs, GitHub, Lovable, sites, source control, public documentation.
2. Internet: IPv4/IPv6, ASNs, BGP, routing, ISPs, TLS, Tor onion services, peer-to-peer and mesh overlays; only authorized observations.
3. Blockchains: Bitcoin mainnet, Lightning channels, Liquid sidechain, Ethereum and other explicitly supported networks; keep their consensus systems distinct.
4. Mining: SoloFury, OCEAN/DATUM, Foundry USA, AntPool, F2Pool, ViaBTC, Braiins, Luxor, SpiderPool, MARA, Solo CKPool, CloverPool, SECPOOL, TrustPool, Poolin, Binance Pool, NiceHash, Kryptex, unMineable; proposed PARADOX Mining. Record pool-reported hashrate separately from independently verified block data.
5. Identity and cryptography: public keys, signatures, SHA-256, Merkle commitments, OpenTimestamps, RFC3161, X.509, proof-of-control challenges, authorization, provenance, Guardian default-deny.
6. Compute and AI: BRIAN², Lucky7 AI, seven verification roles, forty-role design team, Q49/GF49, ARM64 VM, Paradox OS/Zero, Phoenix recovery, versioned releases, agent receipts.
7. Devices and infrastructure: Mac/Termux/Linux/Windows, ARM64 VMs, containers, storage, databases, backups, Tor services, authorized Gateway servers.
8. Organizations and assets: corporate entities, licenses, ownership percentages and voting rights only when documentary evidence supports them; wallets, tokens, accounts and physical assets require distinct proof of control and legal ownership.
9. Communications: Telegram, authenticated channels/bots, email, webhooks, event logs and signed notifications; no secret token exposure.
10. Science and research: mathematical proofs, simulations, quantum models, experimental protocols, falsifiable hypotheses; do not conflate simulation with physical reality.
11. Governance and recovery: Guardian, approvals, 7-of-7 concepts, change management, incident response, Phoenix recovery, independent audit.
12. Timeline and evidence: UTC, source capture, canonical SHA-256, reversible transforms, signed receipts, append-only versioned ledgers, negative tests, independent rechecks.

## Traversal

End -> prerequisites -> origin; origin -> measured actions -> independently verified outcomes. Graph search is bounded, rate-limited, permission-aware and read-only by default. Do not crawl the entire internet, infer common ownership from co-occurrence, or assert control of third-party services.

## Evidence gates

PASS only for actually executed and reproducible checks; FAIL for observed negative results; PENDING for untested, unreachable, or unsupported. Separate LOCAL, PUBLIC-API-OBSERVED, INDEPENDENTLY-VERIFIED, and DEPLOYED states. Public blockchain explorer data is an observation, not an independent full-node consensus check.

## Hard constraints

Testnet permanently excluded unless user explicitly changes policy. No wallet signing, fund movement, broadcasting, private-key disclosure, device changes, unapproved deployments, or modification of originals. Preserve earlier releases. New systems require explicit authorization and independently checked receipts before marking LIVE.

## Next implementation gates

Schema validation and deterministic graph fingerprint; evidence ingestion adapters; source-specific read-only checks; independent Bitcoin and Liquid verification; authorized Tor/Lightning peer setup; Lovable build when credits allow; owner approval for deployment.
