"""Opt-in Auvik live read-only smoke check.

Requires explicit enablement and owner-provisioned environment credentials.
Prints only counts and response digests; never emits raw tenant/device records.
"""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone

from auvik_readonly import AuvikReadOnly

def _items(payload):
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
    if isinstance(payload, list):
        return payload
    return []

def redacted_summary(payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return {
        "record_count": len(_items(payload)),
        "response_sha256": hashlib.sha256(canonical).hexdigest(),
    }

def run():
    if os.getenv("PARADOX_AUVIK_READ_ONLY", "false").lower() != "true":
        raise RuntimeError("Live check blocked: set PARADOX_AUVIK_READ_ONLY=true explicitly")
    client = AuvikReadOnly()
    started = datetime.now(timezone.utc).isoformat()
    result = {
        "schema": "PARADOX-AUVIK-READONLY-SMOKE-v1",
        "started_at": started,
        "live_api_calls": True,
        "operations": {},
    }
    client.verify_credentials()
    result["operations"]["credential_verification"] = {"status": "PASS"}
    tenants = client.list_tenants(page_first=100)
    result["operations"]["tenant_inventory"] = {"status": "PASS", **redacted_summary(tenants)}
    tenant_id = os.getenv("AUVIK_TENANT_ID")
    if tenant_id:
        devices = client.list_devices(tenant=tenant_id, page_first=100)
        result["operations"]["device_inventory"] = {"status": "PASS", **redacted_summary(devices)}
    else:
        result["operations"]["device_inventory"] = {
            "status": "NOT_RUN",
            "reason": "Set AUVIK_TENANT_ID to a tenant authorized for this service account",
        }
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, sort_keys=True, indent=2))
    return result

if __name__ == "__main__":
    run()
