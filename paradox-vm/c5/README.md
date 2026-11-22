# S7 Meta Anchor and Return Protocol (C5)

Each of seven registered S7 agent identities owns an independent, persistent
home Meta address. A jump or skip-hop records origin, destination, immutable
home address, monotonically increasing logical sequence, and a SHA-256
hash-linked audit record. Return-home writes a new explicit transition back
to the registered home; it never erases travel history.

## Run
```sh
python -m unittest -v
```

## Safety and scope
- This is a deterministic local protocol model, not a live network or a claim
  that seven autonomous agents are running.
- Namespaces model parallel spaces; W is a fourth integer coordinate.
- `logical_time` is an event sequence, not time travel or a synchronized
  physical clock.
- Destination namespaces must be explicitly authorized.
- SHA-256 hash chaining detects accidental/tampered history only if the
  trusted checkpoint is protected; it is not a digital signature or identity
  proof. Production requires authenticated agent keys, signed checkpoints,
  durable storage, shared replay protection, peer authentication and recovery
  testing at both ends.
- No external system is contacted and no live-world action is performed.
