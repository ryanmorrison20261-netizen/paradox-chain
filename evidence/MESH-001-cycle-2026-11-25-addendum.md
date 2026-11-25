# MESH-001 5×5 Cycle — Run 2 Addendum

Observed at UTC: 2026-11-25T02:14:19.625Z  
Repository: ryanmorrison20261-netizen/paradox-chain  
Existing audit branch: audit/mesh-001-5x5-2026-11-24  
Existing draft PR: https://github.com/ryanmorrison20261-netizen/paradox-chain/pull/6  
Raw evidence snapshot: evidence/MESH-001-cycle-2026-11-25-raw.json  
Raw snapshot SHA-256: 009fe53a2c60e873fc2fa620fd53d98b97cb951048b4ff8f0fdd5af35d3d7f54  
Raw snapshot commit: e0b8e6db8b74f5cfc2eae1639307cd8465a2422e

## Decision

**MESH-001 remains BLOCKED / PARTIAL.** This run advances the existing audit branch, refreshes the six-repository branch inventory, re-reads source and workflow evidence, retries the three previously failing workflows, and preserves the current source snapshots. It does not establish live Bitcoin/Lightning connectivity, a live federated mesh, real five-party approvals, or independent live end-to-end acceptance.

## Agent accounting

- Actually active: Repository Audit Agent (this audit execution).
- Actual test executors: GitHub-hosted Actions runners for the cited historical workflow runs and the accepted retry attempts.
- All other named reviewer/operator roles are planned assignments, not verified active autonomous agents.
- No independent external auditor or seven-agent runtime was verified.

## Strict 5×5 matrix — 25 checks

| Check | Dimension / concrete check | One accountable role | Result | Evidence / handoff |
|---|---|---|---|---|
| 1.1 | Source: verify existing PR #6 state, base, head and merge status | Repository Audit Agent (active) | PASS | PR #6 remains open, draft, mergeable, unmerged; base main; head audit/mesh-001-5x5-2026-11-24 at 67725b75670652942ac302a5b8d810f304b26bb2 |
| 1.2 | Source: enumerate branches across the six established repositories | Branch Lineage Auditor (planned) | PASS | 30 branches: metaparadox-site 5; hackerai2 3; paradox-mini 1; paradox-os-vm 13; paradox-identity 2; paradox-chain 6. New audit branch accounts for the increase from 29 to 30 |
| 1.3 | Source: verify branch-protection state for all 30 branches | Repository Protection Auditor (planned) | BLOCKED | Prior inventory recorded 29 branches as unprotected. Current branch-search response exposes names only; protection state for the new audit branch was not returned. No protection claim made |
| 1.4 | Source: preserve and re-hash the six relevant source snapshots | Source Integrity Auditor (planned) | PASS | Raw source contents stored in the raw JSON snapshot. SHA-256 values match the prior manifest for txcheck.py, chainverify.py, openapi.yaml, SECURITY.md and chain-hosts.deny; layer2_growth.py also hashed |
| 1.5 | Source: reconcile MH-001–MH-008 provenance and locate original source artifacts | MH Register Reconciler (planned) | BLOCKED | Prior conversation register confirms the eight working labels and definitions. No corresponding issue records were found in the six Paradox repositories; no canonical repository artifact or original per-record hashes surfaced |
| 2.1 | Live data: inspect producer adapter for both explorer sources and tip/transaction reads | Explorer Adapter Reviewer (planned) | PASS | txcheck.py declares mempool.space and blockstream.info and reads transaction and tip endpoints; source inspection only |
| 2.2 | Live data: request current mempool.space tip height | Mempool API Observer (planned) | BLOCKED | GET attempted; URL inaccessible through the available web path; no HTTP status or response body |
| 2.3 | Live data: request current blockstream.info tip height | Blockstream API Observer (planned) | BLOCKED | GET attempted; URL inaccessible through the available web path; no HTTP status or response body |
| 2.4 | Live data: verify Bitcoin Core read-only RPC identity and height | Bitcoin Core RPC Operator (planned; not activated) | BLOCKED | No configured node endpoint, RPC credentials or authorized target |
| 2.5 | Live data: verify Lightning read-only node identity and health | Lightning Integration Operator (planned; not activated) | BLOCKED | No Lightning URI or credentials; reviewed Layer-2 ledger explicitly states it does not connect to Lightning or move funds |
| 3.1 | Architecture: verify producer-side transaction/tip contract | Producer Contract Reviewer (planned) | PASS | Source declares both explorer endpoints, transaction lookup and tip-height lookup; no live request was successful |
| 3.2 | Architecture: verify consumer-side Bitcoin header validation contract | Consumer Contract Reviewer (planned) | PASS | chainverify.py checks genesis, previous-header linkage, proof of work, difficulty retargets, median-time-past and version activation rules |
| 3.3 | Architecture: verify Meta Mesh API destination exists | API Destination Reviewer (planned) | BLOCKED | OpenAPI server remains https://api.example.invalid/v1, explicitly a placeholder; no deployed consumer endpoint |
| 3.4 | Architecture: verify VM guest can reach both explorer producers | VM Boundary Reviewer (planned) | BLOCKED | SECURITY.md sets guest networking to restricted/default-deny; chain-hosts.deny sinks both explorer hosts. Preserve isolation; no bypass attempted |
| 3.5 | Architecture: verify local Layer-2 ledger enforces both-end receipts | Layer-2 Contract Reviewer (planned) | PASS | layer2_growth.py requires both_ends_verified, source_receipt and destination_receipt; it remains a local proof state machine, not a live Lightning adapter |
| 4.1 | Agents: verify actual seven-agent runtime and accountable handoffs | Agent Runtime Coordinator (planned) | BLOCKED | Only Repository Audit Agent was active in this run. Seven logical roles are not seven active autonomous agents |
| 4.2 | Security: verify real five-party signer identities and approvals | PKI Identity Steward (planned) | BLOCKED | Existing DER suite uses synthetic fixtures; real role binding and four additional signer approvals remain unverified |
| 4.3 | Security: verify C4 replay, sequencing, frame bounds and mutual TLS | C4 Security Reviewer (planned) | PASS | Existing C4 secure-connections CI job is successful; test result is local loopback, not an external peer |
| 4.4 | Security: verify guest default-deny and explorer deny-list controls | Guardian Policy Auditor (planned) | PASS | SECURITY.md and chain-hosts.deny both confirm restricted/default-deny behavior and deny entries for mempool.space and blockstream.info |
| 4.5 | Authorization: verify prohibited actions were not performed | Change Approval Gatekeeper (planned) | PASS | No deployment, transaction broadcast, spending, live-key signing, listener exposure or firewall relaxation. Only repository reads, CI retry requests and audit-evidence commits occurred |
| 5.1 | Tests/evidence: re-read C4 secure-connections workflow result | C4 CI Evidence Auditor (planned) | PASS | Run 44985863182, job 137096149002: 40 tests; GitHub job and test step successful |
| 5.2 | Tests/evidence: re-read C4 topology workflow result | C4 Topology Evidence Auditor (planned) | PASS | Run 44985863188, job 137096148962: 40 tests; GitHub job and test step successful |
| 5.3 | Tests/evidence: re-read C5 durable-recovery workflow result | C5 CI Evidence Auditor (planned) | PASS | Run 44986200750, job 137097193698: 17 tests; GitHub job and test step successful |
| 5.4 | Tests/evidence: re-read DER multi-auth workflow result | Crypto Evidence Auditor (planned) | PASS | Run 44985301492, job 137094466181: 30 synthetic fixture tests; GitHub job and test step successful |
| 5.5 | Tests/evidence: retry and adjudicate Q49, VM and Meta Guardian failures | Q49/Guardian Failure Adjudicator (planned) | FAIL | Retry requests were accepted. Latest jobs still concluded failure; step details were empty and raw log fetches returned BlobNotFound. Root cause remains unknown |

**Matrix totals: 14 PASS · 10 BLOCKED · 1 FAIL.** PASS here means the specific local/static/CI check passed, not that MESH-001 acceptance passed.

## Detailed test records

Run-local test IDs below are audit identifiers for this cycle only; they do not replace or rename MH-001–MH-008.

### MESH001-20261125-R2-BRANCH-INVENTORY
- Test ID: MESH001-20261125-R2-BRANCH-INVENTORY
- Accountable agent: Repository Audit Agent (active)
- Input/environment: GitHub branch-search API; six established repositories; paginated branch-name responses
- UTC execution timestamp: 2026-11-25T02:14:19.625Z
- Expected result: complete branch inventory for all six target repositories
- Actual result: 30 branch names returned; counts 5, 3, 1, 13, 2 and 6
- Evidence hash: 8b1e72df491c5715b10b9dbc9be25520d0137c4e1b06f4504702e95ebc9e083d
- Independent verification result: six repository responses re-read; count sum independently recomputed from returned branch-name arrays; branch-protection flags were not exposed
- Status: PASS

### MESH001-20261125-R2-SOURCE-SNAPSHOT
- Test ID: MESH001-20261125-R2-SOURCE-SNAPSHOT
- Accountable agent: Source Integrity Auditor (planned; executed by Repository Audit Agent)
- Input/environment: six fetched source files from paradox-chain main, paradox-os-vm main, Foundry feature branch and commit 58f471535f6e9f90857e6a53c9099dd692145d76
- UTC execution timestamp: 2026-11-25T02:14:19.625Z
- Expected result: raw source content preserved and SHA-256 values reproducible
- Actual result: six source contents stored in the raw JSON snapshot; five hashes match the prior manifest and the Layer-2 file hash is recorded
- Evidence hash: 009fe53a2c60e873fc2fa620fd53d98b97cb951048b4ff8f0fdd5af35d3d7f54
- Independent verification result: raw JSON fetched back from GitHub and its SHA-256 recomputed; exact match
- Status: PASS

### MESH001-20261125-R2-SHA256-KAT
- Test ID: MESH001-20261125-R2-SHA256-KAT
- Accountable agent: Evidence Integrity Auditor (planned; executed by Repository Audit Agent)
- Input/environment: SHA-256 known-answer input UTF-8 string abc
- UTC execution timestamp: 2026-11-25T02:14:19.625Z
- Expected result: ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
- Actual result: exact digest match
- Evidence hash: ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
- Independent verification result: digest compared byte-for-byte with the published SHA-256 known-answer value
- Status: PASS

### MESH001-20261125-R2-PRODUCER-STATIC
- Test ID: MESH001-20261125-R2-PRODUCER-STATIC
- Accountable agent: Producer Contract Reviewer (planned)
- Input/environment: paradox-chain main, tx-verifier/tools/txcheck.py
- UTC execution timestamp: 2026-11-25T02:14:19.625Z
- Expected result: source contains both independent explorer hosts and transaction/tip read paths
- Actual result: both hosts and both read paths present; source inspection only, no live request
- Evidence hash: 7ad915498f588c56bf2f96897cd4d93733253ec664af95b5e8fac73a4f16e463
- Independent verification result: SHA-256 matches prior manifest; no separate external reviewer
- Status: PASS

### MESH001-20261125-R2-CONSUMER-STATIC
- Test ID: MESH001-20261125-R2-CONSUMER-STATIC
- Accountable agent: Consumer Contract Reviewer (planned)
- Input/environment: paradox-chain main, tx-verifier/tools/chainverify.py
- UTC execution timestamp: 2026-11-25T02:14:19.625Z
- Expected result: verifier checks genesis, linked headers, proof of work, retargets, MTP and activation rules
- Actual result: required checks are present in source; no fresh full-chain fixture execution was run in this cycle
- Evidence hash: 36ef456718acd1e360002f632af161e904563d43359ccfb261d10097d79b05bb
- Independent verification result: SHA-256 matches prior manifest; source review only
- Status: PASS

### MESH001-20261125-R2-L2-BOTH-ENDS-STATIC
- Test ID: MESH001-20261125-R2-L2-BOTH-ENDS-STATIC
- Accountable agent: Layer-2 Contract Reviewer (planned)
- Input/environment: paradox-os-vm commit 58f471535f6e9f90857e6a53c9099dd692145d76, tools/layer2_growth.py
- UTC execution timestamp: 2026-11-25T02:14:19.625Z
- Expected result: local state machine refuses forward/backward proof records unless both source and destination receipts are present
- Actual result: both_ends_verified, source_receipt and destination_receipt gates are present; module explicitly does not connect to Lightning or move funds
- Evidence hash: 83762b3295f127010f0d78a8f8cc008f57800f600d12e04520f4f7295b7c0090
- Independent verification result: raw file hash re-read from the stored snapshot; source inspection only, no live channel
- Status: PASS

### MESH001-20261125-R2-VM-EGRESS
- Test ID: MESH001-20261125-R2-VM-EGRESS
- Accountable agent: Guardian Policy Auditor (planned)
- Input/environment: paradox-os-vm main, SECURITY.md and recipe/guest/chain-hosts.deny
- UTC execution timestamp: 2026-11-25T02:14:19.625Z
- Expected result: default-deny/restricted guest policy and explicit deny entries for both public explorers
- Actual result: all controls and both host entries present
- Evidence hash: 0451ec2c5490880e7feaa166d8c0144a129a5f14c415401e58bf36c8237d3789
- Independent verification result: both source files independently re-fetched and their SHA-256 values match the prior manifest
- Status: PASS

### MESH001-20261125-R2-OPENAPI-DESTINATION
- Test ID: MESH001-20261125-R2-OPENAPI-DESTINATION
- Accountable agent: API Destination Reviewer (planned)
- Input/environment: paradox-os-vm Foundry feature branch, api/openapi.yaml
- UTC execution timestamp: 2026-11-25T02:14:19.625Z
- Expected result: a configured, reachable API destination
- Actual result: server URL is api.example.invalid and is explicitly marked placeholder; no service is deployed
- Evidence hash: f741e3c422eb87d870d8aa0d48c02ecf195770c047eb8ba590f13c5eb9524628
- Independent verification result: file re-fetched from the same branch and hash matches prior manifest; no live service probe possible
- Status: BLOCKED

### MESH001-20261125-R2-MEMPOOL-TIP
- Test ID: MESH001-20261125-R2-MEMPOOL-TIP
- Accountable agent: Mempool API Observer (planned)
- Input/environment: GET https://mempool.space/api/blocks/tip/height via available web access path
- UTC execution timestamp: 2026-11-25T02:10:31.121Z (observation time; exact request-start time not exposed)
- Expected result: HTTP 200 and a numeric current tip height
- Actual result: URL inaccessible through this path; no HTTP status or response body
- Evidence hash: 79072887a617b78738bbdbd7667ffe6c904b4a880df4de258cf6e6445e0b225a
- Independent verification result: no live response; previous attempt descriptor remains separately recorded in the prior audit
- Status: BLOCKED

### MESH001-20261125-R2-BLOCKSTREAM-TIP
- Test ID: MESH001-20261125-R2-BLOCKSTREAM-TIP
- Accountable agent: Blockstream API Observer (planned)
- Input/environment: GET https://blockstream.info/api/blocks/tip/height via available web access path
- UTC execution timestamp: 2026-11-25T02:10:31.121Z (observation time; exact request-start time not exposed)
- Expected result: HTTP 200 and a numeric tip height consistent with an independent explorer
- Actual result: URL inaccessible through this path; no HTTP status or response body
- Evidence hash: eed1818cff7eb2c79abb0f8a65ec4c4bbdbca41fea725a9ce7eb78ac1b87f953
- Independent verification result: no live response and no cross-source agreement
- Status: BLOCKED

### MESH001-20261125-R2-CORE-RPC
- Test ID: MESH001-20261125-R2-CORE-RPC
- Accountable agent: Bitcoin Core RPC Operator (planned; not activated)
- Input/environment: read-only getblockchaininfo/getblockcount; no configured node URI or credentials
- UTC execution timestamp: 2026-11-25T02:14:19.625Z (blocked assessment; not executed)
- Expected result: authenticated node returns chain identity and height
- Actual result: not run; endpoint and credentials absent
- Evidence hash: b2a387bba8be518d640a6b18202a8e31a6e87df5a140d75b41d3b040a6e7eef5
- Independent verification result: SECURITY.md confirms guest isolation from blockchain endpoints; no node contacted
- Status: BLOCKED

### MESH001-20261125-R2-LIGHTNING-HEALTH
- Test ID: MESH001-20261125-R2-LIGHTNING-HEALTH
- Accountable agent: Lightning Integration Operator (planned; not activated)
- Input/environment: authenticated read-only Lightning node health; no node URI or credentials
- UTC execution timestamp: 2026-11-25T02:14:19.625Z (blocked assessment; not executed)
- Expected result: authenticated node identity and health response
- Actual result: not run; source code describes a local-only proof ledger
- Evidence hash: 83762b3295f127010f0d78a8f8cc008f57800f600d12e04520f4f7295b7c0090
- Independent verification result: no endpoint/credentials available to challenge
- Status: BLOCKED

### GitHub Actions run 44985863182 — C4 secure-connections
- Test ID: 44985863182 / job 137096149002
- Accountable agent: C4 Transport Test Owner (planned; Actions runner executed)
- Input/environment: paradox-chain C4 feature commit 02864828f2de7d8bbdd941bc4a489b4b6ef30a5e; ubuntu-latest; Python 3.12
- UTC execution timestamp: 2026-11-22T04:37:25.310694Z
- Expected result: transport, replay, peer identity and local mTLS loopback tests pass
- Actual result: 40 tests in 0.281 s; OK; job and test step success
- Evidence hash: da8128957ffadf1e60d97471969d76e60e24d4cbe1cd6de4582b8bcfcd38d3fc
- Independent verification result: job and step metadata re-read from GitHub; no external peer or third-party review
- Status: PASS

### GitHub Actions run 44985863188 — C4 topology
- Test ID: 44985863188 / job 137096148962
- Accountable agent: C4 Topology Test Owner (planned; Actions runner executed)
- Input/environment: paradox-chain C4 feature commit 02864828f2de7d8bbdd941bc4a489b4b6ef30a5e; ubuntu-latest; Python 3.12
- UTC execution timestamp: 2026-11-22T04:37:25.927573Z
- Expected result: route authorization, topology and delivery tests pass
- Actual result: 40 tests in 0.256 s; OK; job and test step success
- Evidence hash: 6a12551e0364eb477497a8f90c9f06fc443c2d654b6bea6637f0859ee14d1317
- Independent verification result: job and step metadata re-read from GitHub; no external mesh
- Status: PASS

### GitHub Actions run 44986200750 — C5 durable recovery
- Test ID: 44986200750 / job 137097193698
- Accountable agent: C5 Recovery Test Owner (planned; Actions runner executed)
- Input/environment: paradox-chain C5 feature commit fe599fc8453286a0ba819de704069346aa1051a4; ubuntu-latest; Python 3.12.16
- UTC execution timestamp: 2026-11-22T04:42:16.264983Z
- Expected result: save/restore, hash-chain replay and tamper rejection pass
- Actual result: 17 tests in 0.005 s; OK; job and test step success
- Evidence hash: c0725870436a79e0b2b2942164bba005fd99a98107056cfd5380a6f90468cf3b
- Independent verification result: job and step metadata re-read from GitHub; no shared multi-host store or identity signature
- Status: PASS

### GitHub Actions run 44985301492 — DER multi-auth
- Test ID: 44985301492 / job 137094466181
- Accountable agent: Five-Party Crypto Test Owner (planned; Actions runner executed)
- Input/environment: paradox-chain DER feature commit 36055371a45ac916018b384991c7190998bc2b9a; ubuntu-latest; Python 3.12; synthetic DER/secp256k1 fixtures
- UTC execution timestamp: 2026-11-22T04:30:06.832426Z
- Expected result: canonical envelope, distinct keys, DER signatures, nonce binding and tamper rejection pass
- Actual result: 30 synthetic tests; OK; job and test step success
- Evidence hash: ddbd12cdad1c9db024b621152469ef297699e9f961c8fffce2fb663d1b9ae2ae
- Independent verification result: job and step metadata re-read from GitHub; synthetic fixtures do not prove real five-party approval
- Status: PASS

### GitHub Actions run 44975900516 — Q49 retry
- Test ID: 44975900516-R2 / jobs 138925779655 and 138925779884
- Accountable agent: Q49 Security Test Owner (planned; Actions runners executed)
- Input/environment: paradox-os-vm commit 58f471535f6e9f90857e6a53c9099dd692145d76; Q49 Security and Asset Audit workflow
- UTC execution timestamp: retry execution time not exposed by connector; latest failure observed 2026-11-25T02:11:46.456Z
- Expected result: OpenSSL source build and Q49 evidence jobs succeed
- Actual result: both latest jobs concluded failure; job-step details empty; raw log fetch returned NOT_FOUND BlobNotFound
- Evidence hash: ad4686109554f254bdb3581a57cb9d6303e3c2792da241e1a451f2cb28a11722
- Independent verification result: GitHub job metadata re-read and confirms failure; no raw log or failing step available to establish root cause
- Status: FAIL

### GitHub Actions run 44975900472 — VM test retry
- Test ID: 44975900472-R2 / job 138925788237
- Accountable agent: VM Test Owner (planned; Actions runner executed)
- Input/environment: paradox-os-vm commit 58f471535f6e9f90857e6a53c9099dd692145d76; installer tests and secret scan
- UTC execution timestamp: retry execution time not exposed by connector; latest failure observed 2026-11-25T02:11:46.456Z
- Expected result: installer unit/integration suite and secret scan succeed
- Actual result: latest job concluded failure; job-step details empty; raw log fetch returned NOT_FOUND BlobNotFound
- Evidence hash: 0482e1fd386172aa4d6b1a8aaeea81643a7b0c57b86eee3c6fae6f570b849104
- Independent verification result: GitHub job metadata re-read and confirms failure; root cause unknown
- Status: FAIL

### GitHub Actions run 44975896194 — Meta Guardian retry
- Test ID: 44975896194-R2 / job 138925801879
- Accountable agent: Meta Guardian Test Owner (planned; Actions runner executed)
- Input/environment: paradox-os-vm commit 58f471535f6e9f90857e6a53c9099dd692145d76; readiness workflow
- UTC execution timestamp: retry execution time not exposed by connector; latest failure observed 2026-11-25T02:11:46.456Z
- Expected result: readiness checks pass or report explicit blockers
- Actual result: latest job concluded failure; job-step details empty; raw log fetch returned NOT_FOUND BlobNotFound
- Evidence hash: 407a436b2ce5d9dd40957e2477083838beb2addd42c621f8af1695e2a41ed3e1
- Independent verification result: GitHub job metadata re-read and confirms failure; root cause unknown
- Status: FAIL

## MH-001–MH-008 reconciliation

The prior conversation execution register, dated 2026-11-23, is the source of the existing MH labels and definitions. These are working register identifiers from the prior conversation, not verified GitHub issue numbers. Preserve them exactly; do not create replacements.

| Existing record | Original register definition | Prior status | Current reconciled status |
|---|---|---|---|
| MH-001 | Repository discovery | Partial | PARTIAL — 24 accessible account repositories were previously visible; six target repositories are confirmed; full audit of all 24 remains incomplete |
| MH-002 | Branch inventory | Incomplete | COMPLETE for the six target repositories: 30 branches now inventoried. Protection status for the newly added audit branch remains unverified; the prior 29 were reported unprotected |
| MH-003 | Source/dependency inspection | Partial | PARTIAL — source prototypes and security boundaries inspected; API remains a placeholder and live integrations remain blocked |
| MH-004 | Meshhub repository creation | Blocked | BLOCKED — no Meshhub repository created; no replacement repository substituted |
| MH-005 | Ten field interfaces | Specified | SPECIFIED / NOT IMPLEMENTED — no deployed runtime |
| MH-006 | Bitcoin indexing | Not started | PROTOTYPE FOUND / LIVE INDEXING NOT STARTED — explorer adapter and header verifier source exist; no current live indexer or Core RPC connection |
| MH-007 | Q49 / Guardian / HoloMem integration | Not started | COMPONENTS PARTIAL / LIVE INTEGRATION NOT VERIFIED — three latest workflow retries failed; no live HoloMem integration evidence |
| MH-008 | Independent end-to-end tests | Not started | NOT STARTED — local CI passes do not establish independent live E2E |

MESH-001 remains the umbrella acceptance gate across MH-001 through MH-008; it is not a replacement for any of them. The conversation register preserves the prior definitions, but original per-record source artifacts and evidence hashes are still absent.

## Next five dependencies

1. Recover the original MH register source/evidence artifact if it exists outside the six inspected repositories and prior conversation register; preserve the original identifiers and provenance.
2. Obtain the Q49, VM and Meta Guardian raw job logs from GitHub Actions or the repository owner, identify the first failing step, repair only that cause, then rerun.
3. Keep VM guest default-deny; provision an explicitly approved host-side read-only explorer adapter and capture fresh raw Mempool/Blockstream responses with UTC timestamps and hashes.
4. Provision approved CA/node identities, trusted peer/address registry and shared replay storage; execute an external two-node C4 test with a genuinely independent reviewer.
5. Provision a read-only Bitcoin Core and Lightning endpoint only after operator authorization; then test producer and consumer ends, source/destination receipts, recovery, replay rejection and independent E2E verification.

## Safety and acceptance boundary

No transaction was broadcast, no assets were spent, no live key was used, no deployment was performed, and no firewall or guest-isolation rule was weakened. The accepted GitHub Actions retry requests were limited to rerunning existing failed jobs. No official victory or MESH-001 end-to-end PASS is claimed.
