# PARADOX Tor Onion Evidence Node v1

A read-only evidence-node prototype for Tor v3. Four local checks passed (policy, Tor loopback configuration, no secret-named files, HTTP health/404). The first HTTP test failed because port 8080 was occupied; the test was repaired to use a free port and then passed. No live Tor onion service was started or externally tested.

Node package: available as PARADOX Onion Node v1 ZIP in the accompanying ChatGPT release conversation. Components: Python HTTP server, evidence.json, static HTML, torrc, tests, SHA256SUMS.

## Host setup

On a Linux server you administer, install Python 3 and Tor. Run `python3 node.py` from the package. In the host's existing torrc, **merge**, do not overwrite, these lines:

```text
HiddenServiceDir /var/lib/tor/paradox/
HiddenServiceVersion 3
HiddenServicePort 80 127.0.0.1:8080
```

Restart Tor only after reviewing existing services and permissions. Read the generated onion hostname from the Tor HiddenServiceDir on that host; verify accessibility from an independent Tor client before sharing the hostname. Never publish the onion private key.

## Safety and status

Guardian default-deny; testnet blocked; no wallet signing, transfers, broadcast, or private administration. Ownership, independently trusted timestamps, physical breakthroughs, and onion reachability remain NOT PROVEN. Historical encryption signature failure remains unresolved.

Public evidence: [2026-11-20 report](../evidence/public-evidence-status-2026-11-20.md).
