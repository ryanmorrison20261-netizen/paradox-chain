# C3 — Infinite 343 Lattice

C3 defines a finite rule system for an unbounded, recursively addressable 3D
lattice. It is mathematical/computational, not evidence of physically existing
parallel universes.

## Arithmetic
- 7 × 7 × 7 = 343 cells per block.
- Each fixed-z layer is 7 × 7 = 49 ways.
- Seven layers partition each block: 7 × 49 = 343.
- Each cell can address a child 343-cell block, recursively, without a fixed
  maximum hierarchy depth.
- The ambient lattice uses integer coordinates in all directions, including
  negative coordinates.

## Run
```sh
cd paradox-vm/c3
python -m unittest -v
```

## Scaling and safety
The implementation generates cells on demand. It does not materialize an
infinite universe. `expand(address, depth)` materializes a finite frontier of
343^depth addresses and is intended only for modest depths; use iterators and
individual child addressing for larger exploration. No network, physical
world, financial, or autonomous deployment actions are performed.
