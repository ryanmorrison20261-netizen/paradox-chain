# MetaParadox Auvik connector (read-only)

## Scope
This is a **new, isolated integration**. It does not modify the Coinbase adapters or Paradox VM. It reads:
- Auvik credential verification: `GET /authentication/verify`
- Tenant inventory: `GET /v1/tenants`
- Device inventory v1: `GET /v1/inventory/device/info`
- Device inventory v2: `GET /v2/api/inventory/device/info` (opt-in method)

The v1 device endpoint uses the documented plural `tenants` parameter. The v2 method uses the singular `tenant` parameter and defaults to a maximum page size of 1000, per Auvik's migration guide.

## Configuration
Use a dedicated Auvik service account with only the required read permissions. Store credentials in a secret manager or local environment—not Git, logs, issue comments, or chat.

```bash
export PARADOX_AUVIK_READ_ONLY=true
export AUVIK_USERNAME='service-account@example.com'
export AUVIK_API_KEY='...'
export AUVIK_REGION='us1' # match the region shown in the Auvik dashboard
```

```python
from auvik_readonly import AuvikReadOnly
api = AuvikReadOnly()
api.verify_credentials()
tenants = api.list_tenants()
devices = api.list_devices(tenant="TENANT_ID")
# Optional newer v2 inventory:
devices_v2 = api.list_devices_v2(tenant="TENANT_ID")
```

## Security controls
- Disabled by default; explicit enable flag required.
- HTTPS only; host constrained to `auvikapi.<region>.my.auvik.com`.
- Basic authentication is sent only in the Authorization header.
- Fixed GET-only endpoint allowlist. No generic request method.
- Redirects are not followed automatically; HTTP 308 requires region review to avoid forwarding credentials unexpectedly.
- No automatic retry on 400/401/403/404/429; errors are sanitized and response bodies are not logged.
- Tenant-scoped queries; bounded page size; no configuration, dismissal, command, remote-support or mutation endpoints.
- No customer payloads or credentials are persisted by this adapter.

## Verification
Mocked unit tests cover disabled-by-default behavior, URL validation, authentication construction, tenant scoping, v1/v2 parameter differences, write-path rejection, error sanitization, pagination bounds and malformed responses. These tests do **not** prove live Auvik connectivity.

## Live validation gate

An opt-in smoke-check runner is provided at `tools/auvik_readonly_smoke.py`. Run it from `tx-verifier` after setting the environment variables below. It verifies credentials, lists tenants, and optionally reads one tenant's devices when `AUVIK_TENANT_ID` is set. It prints only record counts and SHA-256 response digests; it does not print raw customer records. The runner refuses to execute unless the explicit read-only flag is enabled.

```bash
export PARADOX_AUVIK_READ_ONLY=true
python tools/auvik_readonly_smoke.py
```


Live verification requires the account owner's Auvik service-account credentials and region, supplied only through a secure local secret manager/environment. First verify credentials, then read one tenant and a small page of device inventory. Record timestamp, HTTP status, response counts and a redacted digest—not credentials, raw customer inventory, IPs, serials or full API bodies. Independently compare selected device identifiers/status with the Auvik UI or another authorized source on both ends.

## Current status
Connector source and mock tests are implemented on a separate feature branch. Live account access, live API verification, external security review, merge and deployment remain pending.
