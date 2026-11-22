# Paradox VM C2 — deterministic 3-D kinematics

C2 extends the C1 coordinate concept into a 3-D point-kinematics prototype.

## Run

```bash
cd paradox-vm/c2
python -m unittest -v
```

## Included

- Decimal SI coordinates (x, y, z), velocity (m/s), acceleration (m/s²), and elapsed time (s).
- Explicit mm, cm, m, km conversion.
- Constant-acceleration time stepping.
- Optional inclusive world bounds.
- Swept segment-vs-axis-aligned-box collision detection for straight translations.
- Atomic rejection: invalid, out-of-bounds or colliding moves do not change state.
- JSON state persistence with SHA-256 integrity digest and tamper detection.
- Deterministic translation event replay with continuity/result checks.

## Scope and limitations

This is a point-kinematics educational simulator. It is not a full operating-system
virtual machine, rigid-body solver, articulated-body engine, fluid solver, or
validated physical-world digital twin. Collision geometry is static AABBs; there
is no rotation, finite object volume, friction, restitution, gravity, or adaptive
integration. SHA-256 detects accidental/tampered content relative to a trusted
digest, but is not an authenticated signature. State files must be protected
against replacement by an attacker who can rewrite both payload and digest.

All coordinates are SI metres internally. Unit conversion occurs at the API
boundary. No network, credentials, external services, or privileged actions
are needed.
