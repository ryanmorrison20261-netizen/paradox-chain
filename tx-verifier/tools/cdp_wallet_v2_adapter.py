"""Read-only Coinbase CDP Wallet API v2 adapter.

Requires the official `cdp-sdk` Python package. No account creation, signing,
faucet, transfer, swap, or transaction-submission method is exposed here.
"""
from __future__ import annotations
import os
from typing import Any

class IntegrationDisabled(RuntimeError):
    pass

class CDPWalletV2ReadOnly:
    def __init__(self, client: Any | None = None, *, enabled: bool | None = None):
        self.enabled = (os.getenv("PARADOX_CDP_WALLET_READ_ONLY", "false").lower() == "true") if enabled is None else enabled
        self._client = client
        if not self.enabled:
            raise IntegrationDisabled("CDP Wallet adapter disabled; set PARADOX_CDP_WALLET_READ_ONLY=true")
        if self._client is None:
            try:
                from cdp import CdpClient
            except ImportError as exc:
                raise RuntimeError("Install official Coinbase CDP SDK: pip install cdp-sdk") from exc
            self._client = CdpClient()

    async def list_evm_token_balances(self, *, address: str, network: str) -> Any:
        if not address or not network:
            raise ValueError("address and network are required")
        return await self._client.evm.list_token_balances(address=address, network=network)

    async def close(self) -> None:
        close = getattr(self._client, "close", None)
        if close is not None:
            result = close()
            if hasattr(result, "__await__"):
                await result
