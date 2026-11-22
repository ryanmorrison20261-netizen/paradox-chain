"""Read-only Auvik API connector for MetaParadox.

Only fixed, documented GET endpoints are exposed. No alert dismissal, configuration
changes, commands, remote support, or other write/action APIs are implemented.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

class IntegrationDisabled(RuntimeError):
    pass

class AuvikAPIError(RuntimeError):
    def __init__(self, status: int, message: str = "Auvik API request failed"):
        self.status = status
        # Deliberately omit response bodies and URLs: they can contain customer data.
        super().__init__(f"{message} (HTTP {status})")

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class AuvikReadOnly:
    """Minimal Auvik inventory reader; disabled unless explicitly enabled."""

    DEVICE_INFO_V1 = "/v1/inventory/device/info"
    DEVICE_INFO_V2 = "/v2/api/inventory/device/info"
    TENANTS = "/v1/tenants"
    VERIFY = "/authentication/verify"

    def __init__(
        self,
        *,
        username: str | None = None,
        api_key: str | None = None,
        region: str | None = None,
        base_url: str | None = None,
        enabled: bool | None = None,
        timeout: float = 10.0,
        transport: Callable | None = None,
    ):
        self.enabled = (
            os.getenv("PARADOX_AUVIK_READ_ONLY", "false").lower() == "true"
            if enabled is None else enabled
        )
        if not self.enabled:
            raise IntegrationDisabled("Auvik connector disabled; set PARADOX_AUVIK_READ_ONLY=true")
        self.username = username if username is not None else os.getenv("AUVIK_USERNAME")
        self.api_key = api_key if api_key is not None else os.getenv("AUVIK_API_KEY")
        region = region if region is not None else os.getenv("AUVIK_REGION", "us1")
        if not self.username or not self.api_key:
            raise ValueError("AUVIK_USERNAME and AUVIK_API_KEY are required")
        if not re.fullmatch(r"[a-z0-9-]{2,20}", region):
            raise ValueError("Invalid Auvik region")
        candidate = base_url or f"https://auvikapi.{region}.my.auvik.com"
        parsed = urllib.parse.urlparse(candidate)
        if (parsed.scheme != "https" or parsed.username or parsed.password
                or parsed.query or parsed.fragment or parsed.path not in ("", "/")
                or parsed.port not in (None, 443)
                or not re.fullmatch(r"auvikapi\.[a-z0-9-]+\.my\.auvik\.com", parsed.hostname or "")):
            raise ValueError("Auvik base URL must be an HTTPS auvikapi.<region>.my.auvik.com host")
        self.base_url = f"https://{parsed.hostname}"
        self.timeout = timeout
        self._transport = transport or self._urllib_get

    @staticmethod
    def _urllib_get(url: str, headers: dict[str, str], timeout: float):
        request = urllib.request.Request(url, headers=headers, method="GET")
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=timeout) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers or {}), exc.read()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        allowed = {self.VERIFY, self.TENANTS, self.DEVICE_INFO_V1, self.DEVICE_INFO_V2}
        if path not in allowed:
            raise ValueError("Endpoint is not in the read-only allowlist")
        query = urllib.parse.urlencode(
            [(k, str(v)) for k, v in (params or {}).items() if v is not None],
            doseq=True,
        )
        url = self.base_url + path + (("?" + query) if query else "")
        token = base64.b64encode(f"{self.username}:{self.api_key}".encode()).decode("ascii")
        headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/vnd.api+json, application/json",
            "User-Agent": "MetaParadox-Auvik-ReadOnly/1.0",
        }
        status, response_headers, body = self._transport(url, headers, self.timeout)
        if status < 200 or status >= 300:
            # Do not retry 400/401/403/404/429; redirects require operator region review.
            raise AuvikAPIError(status)
        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise AuvikAPIError(status, "Auvik returned a non-JSON response") from None

    def verify_credentials(self) -> Any:
        return self._get(self.VERIFY)

    def list_tenants(self, *, page_first: int = 100) -> Any:
        self._validate_page(page_first)
        return self._get(self.TENANTS, {"page[first]": page_first})

    def list_devices(self, *, tenant: str, page_first: int = 100) -> Any:
        if not tenant or not isinstance(tenant, str):
            raise ValueError("tenant is required")
        self._validate_page(page_first)
        return self._get(self.DEVICE_INFO_V1, {"tenants": tenant, "page[first]": page_first})

    def list_devices_v2(self, *, tenant: str, page_first: int = 1000) -> Any:
        """Opt-in v2 inventory path; uses singular tenant per Auvik migration guidance."""
        if not tenant or not isinstance(tenant, str):
            raise ValueError("tenant is required")
        self._validate_page(page_first)
        return self._get(self.DEVICE_INFO_V2, {"tenant": tenant, "page[first]": page_first})

    @staticmethod
    def _validate_page(value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 1000:
            raise ValueError("page_first must be an integer from 1 to 1000")
