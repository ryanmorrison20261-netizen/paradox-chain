# C4 — Paradox 4D Parallel-Space Mesh

## Model
- Four integer coordinates (x,y,z,w) define the unbounded 4D lattice.
- w is the fourth coordinate; it is not asserted to be physical time.
- Each parallel-space domain has a separate `space_id` namespace.
- Cross-space connectivity is possible only through explicit bridge links.
- A bridge requires authorization, verification and a non-empty evidence reference.
- One 7x7x7x7 hyperblock contains 2,401 addresses: seven w-layers of 343 xyz addresses.
- The graph router uses deterministic breadth-first search.
- Mesh changes are recorded in a SHA-256 hash-linked audit sequence.

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
