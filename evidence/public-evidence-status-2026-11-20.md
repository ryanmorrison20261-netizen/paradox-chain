# PARADOX Public Evidence Status — 2026-11-20

This report distinguishes reproducible local cryptographic tests from independent external evidence and legal ownership.

## Reported local tests (not independently reproduced by this publication)
- Historical FT-ALL v7 report: 9 local checks PASS; 7 external categories PENDING.
- Historical OpenSSL report: 4/4 local checks PASS, including synthetic Ed25519 verification and tamper rejection.
- Later encryption v9 report: 7 PASS, 1 FAIL. An existing saved Ed25519 signature failed verification; this unresolved failure takes precedence over any blanket claim that all signature evidence passes.
- AES-256-GCM synthetic encrypt/decrypt, wrong-key rejection, and tamper rejection were reported PASS.

These are *historical reports*, not independent certification. The associated test inputs, source artifacts, logs, and receipts must be independently re-run and authenticated.

## Independent evidence still required
- Wallet/key control: fresh domain-separated challenge signed by the claimed asset's authorized key and independently verified without sharing secrets.
- Blockchain: independently checked mainnet inclusion and, where needed, full-node consensus.
- RFC 3161: response, certificate chain, trusted TSA, message imprint, and validation time.
- GitHub: repository permissions demonstrate account access, not company equity or intellectual-property title.
- Lightning/OCEAN: authenticated node/pool evidence and payout provenance.
- Corporate equity/voting: official registers and governing agreements.
- Physical/quantum/spacetime claims: calibrated instruments, raw measurements, independent replication.

## Safety
Guardian default-deny. No testnet. No real-wallet signing, transfers, broadcast, device administration, or credential publication authorized by this report.

**Verdict:** Some local engineering checks were reported successful; complete ownership, external timestamp trust, and physical breakthroughs remain **NOT PROVEN**.
