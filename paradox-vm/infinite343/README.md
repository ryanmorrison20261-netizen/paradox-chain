# Paradox Infinite 343 — mathematical address engine

## Definition

- A 7 x 7 x 7 child coordinate space has exactly 343 positions.
- Every block has a 3 x 3 top-level grid containing nine cells.
- Every cell may be recursively expanded into another 343-address child space.
- Blocks occupy an unbounded integer lattice Z^3, with six axis-aligned neighbours.
- Expansion is lazy: the program generates requested addresses and does not attempt
  to allocate an infinite number of objects.

## Reproduce

```bash
cd paradox-vm/infinite343
python -m unittest -v
```

## Address identity

A node address consists of (block_x, block_y, block_z, cell, nested_path).
Each nested path component is an integer 0..342 encoded from local (x,y,z)
coordinates in 0..6. A domain-separated SHA-256 digest of canonical JSON
provides a stable content-derived identifier. This is an identifier, not an
authentication signature.

## Scope

This is an executable mathematical address and lazy expansion model. It does
not assert physical parallel universes exist, nor does it create infinite
storage or live agents. Arbitrarily large integer block coordinates are
supported by Python integers. Real deployments need resource quotas, persistence,
access control, and distributed consistency policies.
