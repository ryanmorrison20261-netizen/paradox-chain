"""Coinbase Advanced Trade read-only adapter.

Uses Coinbase's official coinbase-advanced-py RESTClient. This wrapper deliberately
exposes only read operations. Supply a dedicated VIEW-only CDP API key.
"""
from __future__ import annotations
import os
from typing import Any

class IntegrationDisabled(RuntimeError):
    pass

class AdvancedTradeReadOnly:
    def __init__(self, client: Any | None = None, *, enabled: bool | None = None):
        self.enabled = (os.getenv("PARADOX_ADVANCED_TRADE_READ_ONLY", "false").lower() == "true") if enabled is None else enabled
        if not self.enabled:
            raise IntegrationDisabled("Advanced Trade adapter disabled; set PARADOX_ADVANCED_TRADE_READ_ONLY=true")
        if client is None:
            try:
                from coinbase.rest import RESTClient
            except ImportError as exc:
                raise RuntimeError("Install official Coinbase Advanced SDK: pip install coinbase-advanced-py") from exc
            key = os.getenv("COINBASE_ADVANCED_API_KEY")
            secret = os.getenv("COINBASE_ADVANCED_API_SECRET")
            if not key or not secret:
                raise RuntimeError("Missing Coinbase Advanced API credentials")
            client = RESTClient(api_key=key, api_secret=secret, timeout=10, verbose=False)
        self._client = client

    def list_accounts(self) -> Any:
        return self._client.get_accounts()

    def list_products(self, **kwargs: Any) -> Any:
        return self._client.get_products(**kwargs)

    def get_product(self, product_id: str) -> Any:
        if not product_id:
            raise ValueError("product_id is required")
        return self._client.get_product(product_id=product_id)

    def get_best_bid_ask(self, product_ids: list[str]) -> Any:
        if not product_ids or any(not p for p in product_ids):
            raise ValueError("non-empty product_ids required")
        return self._client.get_best_bid_ask(product_ids=product_ids)

    def get_public_product_book(self, product_id: str) -> Any:
        """Read the unauthenticated public order book for endpoint parity checks."""
        if not product_id:
            raise ValueError("product_id is required")
        return self._client.get_public_product_book(product_id=product_id, limit=1)
