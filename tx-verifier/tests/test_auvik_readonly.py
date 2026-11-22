import base64
import json
import os
import sys
import unittest
from urllib.parse import urlparse, parse_qs
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from auvik_readonly import AuvikReadOnly, IntegrationDisabled, AuvikAPIError

class AuvikReadOnlyTests(unittest.TestCase):
    def transport(self, payload=None, status=200):
        calls = []
        body = json.dumps(payload or {"data": []}).encode()
        def call(url, headers, timeout):
            calls.append((url, headers, timeout))
            return status, {"content-type": "application/json"}, body
        return call, calls

    def test_disabled_by_default(self):
        with self.assertRaises(IntegrationDisabled):
            AuvikReadOnly(username="u", api_key="k")

    def test_requires_credentials(self):
        with self.assertRaises(ValueError):
            AuvikReadOnly(enabled=True, username="", api_key="k")

    def test_rejects_non_auvik_or_http_base_url(self):
        for url in ("http://auvikapi.us1.my.auvik.com", "https://evil.example",
                    "https://user:pass@auvikapi.us1.my.auvik.com"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                AuvikReadOnly(enabled=True, username="u", api_key="k", base_url=url)

    def test_auth_is_basic_and_never_in_url(self):
        transport, calls = self.transport()
        client = AuvikReadOnly(enabled=True, username="person@example.com",
                               api_key="secret", transport=transport)
        client.verify_credentials()
        url, headers, _ = calls[0]
        self.assertEqual(urlparse(url).scheme, "https")
        self.assertNotIn("secret", url)
        expected = base64.b64encode(b"person@example.com:secret").decode()
        self.assertEqual(headers["Authorization"], "Basic " + expected)

    def test_device_v1_scopes_tenant(self):
        transport, calls = self.transport()
        client = AuvikReadOnly(enabled=True, username="u", api_key="k", transport=transport)
        client.list_devices(tenant="tenant-1", page_first=50)
        parsed = urlparse(calls[0][0])
        self.assertEqual(parsed.path, "/v1/inventory/device/info")
        self.assertEqual(parse_qs(parsed.query), {"tenants":["tenant-1"], "page[first]":["50"]})

    def test_device_v2_uses_singular_tenant(self):
        transport, calls = self.transport()
        client = AuvikReadOnly(enabled=True, username="u", api_key="k", transport=transport)
        client.list_devices_v2(tenant="tenant-1")
        parsed = urlparse(calls[0][0])
        self.assertEqual(parsed.path, "/v2/api/inventory/device/info")
        self.assertEqual(parse_qs(parsed.query)["tenant"], ["tenant-1"])
        self.assertNotIn("tenants", parse_qs(parsed.query))

    def test_rejects_write_or_unknown_endpoint(self):
        client = AuvikReadOnly(enabled=True, username="u", api_key="k", transport=self.transport()[0])
        with self.assertRaises(ValueError):
            client._get("/v1/alerts/dismiss/123")

    def test_http_errors_are_sanitized_and_not_retried(self):
        transport, calls = self.transport({"error":"private payload"}, status=401)
        client = AuvikReadOnly(enabled=True, username="u", api_key="secret", transport=transport)
        with self.assertRaises(AuvikAPIError) as caught:
            client.verify_credentials()
        self.assertEqual(caught.exception.status, 401)
        self.assertNotIn("secret", str(caught.exception))
        self.assertNotIn("private payload", str(caught.exception))
        self.assertEqual(len(calls), 1)

    def test_rejects_invalid_page_size_and_missing_tenant(self):
        client = AuvikReadOnly(enabled=True, username="u", api_key="k", transport=self.transport()[0])
        with self.assertRaises(ValueError): client.list_tenants(page_first=0)
        with self.assertRaises(ValueError): client.list_devices(tenant="")

    def test_rejects_non_json_response(self):
        def transport(url, headers, timeout):
            return 200, {}, b"not-json"
        client = AuvikReadOnly(enabled=True, username="u", api_key="k", transport=transport)
        with self.assertRaises(AuvikAPIError): client.verify_credentials()

if __name__ == "__main__":
    unittest.main()
