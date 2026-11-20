# PARADOX ONE — Universal Bridge v4

Date: 2026-11-20. This is a **versioned integration specification and evidence registry**, not a claim of a deployed global mesh or legal ownership.

## Universal registry

| System | Role | Current status | Proof needed |
|---|---|---|---|
| PARADOX | Guardian, evidence ledger, bridge | GitHub development artifacts published | Independently running service |
| SoloFury | User-identified external link | UNVERIFIED | Exact URL, authenticated account/project identity, authorized API access |
| Lovable | Application development platform | CONNECTOR AVAILABLE; new build BLOCKED (workspace credits) | Project list, IDs and permissions, credits for new build |
| Bitcoin | Mainnet settlement evidence | PUBLIC OBSERVATION DESIGN | Independent mainnet RPC verification |
| Lightning | Fast payments and node graph | PUBLIC DATA INTEGRATION DESIGN | Signed node ownership challenge, live channel verification |
| Liquid | Bitcoin sidechain | PUBLIC DATA INTEGRATION DESIGN | Live sidechain observations |
| OCEAN | Mining-related evidence | ASSOCIATED BY USER; UNVERIFIED CONTROL | Authenticated mining account and payouts |
| Telegram | Communication/identity | USER-IDENTIFIED LINK; UNVERIFIED | Authenticated bot/channel identity and permissions |
| Tor | Onion transport | LOCAL NODE PACKAGE REPORTED; NO LIVE ONION HOST | Real onion hostname and independent reachability |

## Guardian

- Read-only by default, no wallet signing, funds movement, broadcast, or unapproved deployment.
- Testnet access permanently blocked unless owner explicitly changes policy.
- Preserve originals, store UTC timestamps, provenance, SHA-256 and reproducible PASS/FAIL/PENDING.
- Every graph edge is VERIFIED, ASSOCIATED or UNVERIFIED; never infer common ownership from a URL or public address.
- Never publish private keys, mnemonic phrases, session tokens or onion service secret keys.

## Next verifiable milestones

1. Resolve SoloFury's exact service/project identifier and obtain authorized proof of control.
2. Query connected Lovable projects when account access permits; new project creation currently blocked by workspace credit limit.
3. Integrate only independently observed API data into a read-only network graph.
4. Deploy only to an explicitly authorized host and verify each node's reachability before marking it LIVE.
