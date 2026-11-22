# C4 — Paradox 4D Parallel-Space Mesh

## Model
- Four integer coordinates (x,y,z,w) define the unbounded 4D lattice.
- w is the fourth coordinate; it is not asserted to be physical time.
- Each parallel-space domain has a separate `space_id` namespace.
- Cross-space connectivity is possible only through explicit bridge links.
- A bridge requires authorization, verification and a non-empty evidence reference.
- One 7x7x7x7 hyperblock contains 2,401 addresses: seven w-layers of 343 xyz addresses.
- The graph router uses deterministic breadth-first search and traverses only links
  explicitly marked authorized and verified.
- Mesh changes are recorded in a SHA-256 hash-linked audit sequence.

## Network layer
See CONNECTIONS.md for the opt-in TLS 1.3 mutual-authenticated peer transport.
connection.py provides certificate-pinned sessions; fabric.py adds topology-wide
neighbor connections and multi-hop forwarding over authorized 4D routes. The
transport is disabled by default and requires operator-managed PKI, peer
registries, listener setup, and shared replay storage for clustered deployments.


## Reproduce
```bash
cd paradox-vm/c4
python -m unittest -v
```

## Security boundary
This is an in-process topology and routing reference implementation. The booleans
and evidence references are policy inputs, not cryptographic proof of remote peer
identity. It does not open network sockets, exchange packets, establish TLS,
or claim live mesh peers. A production transport must add mutual authentication,
signed node identities, replay protection, encrypted channels, rate limits,
resource quotas, revocation and independent endpoint verification before use.

"Parallel spaces" are isolated computational namespaces, not a scientific claim
that physically existing parallel universes have been discovered.
