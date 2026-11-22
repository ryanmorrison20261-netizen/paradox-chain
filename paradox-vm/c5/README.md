# S7 Meta Anchor and Durable Recovery (C5)

Seven independent S7 logical agents each retain a fixed home Meta address.
Every jump, skip-hop, and return-home transition is appended to a SHA-256
hash-linked history. Logical time is a monotonic sequence number, not physical
time travel or a synchronized wall clock.

## Recovery contract

- `skip_hop` validates the complete route and all destination namespaces
  before mutation. A denied or malformed hop leaves state unchanged.
- `checkpoint()` emits schema `paradox-s7-checkpoint-v2`, the full event
  history, current/home addresses, logical sequence, and an outer checkpoint
  digest.
- `save(path)` writes a same-directory temporary file, flushes and fsyncs it,
  then atomically replaces the checkpoint and best-effort fsyncs the directory.
- `MetaAnchor.restore(path)` reloads the checkpoint, validates the outer
  digest, rebuilds the records, and independently replays/verifies the full
  hash chain before returning an anchor.
- Corrupt, unsupported, or tampered checkpoints fail closed. The persisted
  `verified` field is not trusted as proof; restore recomputes verification.

## Run

```sh
python -m unittest -v
```

## Security and deployment boundary

This is a local deterministic recovery protocol, not seven live remote agents.
SHA-256 chaining and checkpoint digests detect modification relative to the
stored data but do not prove who created it: a party able to replace the entire
checkpoint can recompute unkeyed hashes. Production needs per-agent signatures,
protected signing keys, authenticated peer identities, encrypted transport,
durable shared replay protection, backup/restore drills, access controls,
monitoring, and independent verification at both endpoints.

The file writer provides atomic replacement on a single filesystem. It does
not provide distributed consensus, multi-writer locking, rollback protection,
encrypted-at-rest storage, or protection against a privileged host attacker.
Use one writer per agent or add a transactional storage service before
multi-host deployment. No network endpoints or live-world actions are used.
