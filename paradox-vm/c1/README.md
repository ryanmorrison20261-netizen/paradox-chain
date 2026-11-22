# Paradox VM — C1 movement model

C1 is the first deterministic position-state component in the Paradox VM
prototype. It represents a one-dimensional position in SI metres and records
every accepted movement as an append-only in-memory event sequence.

## Reproduce the requested test

From the repository root:

```bash
cd paradox-vm/c1
python movement.py
python -m unittest -v
```

Expected final position: **45 metres** after moving backward 5 metres and
then forward 50 metres from the origin.

## Model and limits

- Uses Python `Decimal` constructed from decimal strings; no binary-float
  rounding is introduced by the movement API.
- Supports optional inclusive minimum and maximum position boundaries.
- Validates a move before changing state; rejected moves do not mutate the
  position or event history.
- Records sequence number, direction, distance, start and end positions.
- This is a deterministic 1-D kinematic state model, not a full virtual
  machine, 3-D simulator, rigid-body physics engine, or live VM deployment.
- SI metre is the default unit. A different physical scale must be explicitly
  defined before interpreting coordinates as real-world travel.

## Verification

Run the standard-library test suite with `python -m unittest -v`.
No network access, credentials, external services, or privileged operations
are required.
