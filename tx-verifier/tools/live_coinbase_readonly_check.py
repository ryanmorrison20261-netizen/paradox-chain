"""Credential-safe, read-only Coinbase live integration smoke test.

Requires explicit credentials and wallet address/network supplied through the
environment. Emits metadata only: never prints credentials, account details,
wallet addresses, token amounts, or raw API responses.
"""
from __future__ import annotations
import asyncio, hashlib, json, os
from datetime import datetime, timezone
from typing import Any
from cdp import CdpClient
from cdp_wallet_v2_adapter import CDPWalletV2ReadOnly
from advanced_trade_readonly import AdvancedTradeReadOnly

REQUIRED = (
    "CDP_API_KEY_ID", "CDP_API_KEY_SECRET",
    "COINBASE_ADVANCED_API_KEY", "COINBASE_ADVANCED_API_SECRET",
    "PARADOX_CDP_EVM_ADDRESS", "PARADOX_CDP_EVM_NETWORK",
)

def safe_mapping(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    converter = getattr(value, "to_dict", None)
    if callable(converter):
        result = converter()
        return result if isinstance(result, dict) else {}
    return {}

def count_items(value: Any, *keys: str) -> int:
    mapped = safe_mapping(value)
    for key in keys:
        candidate = mapped.get(key)
        if candidate is None:
            candidate = getattr(value, key, None)
        if isinstance(candidate, (list, tuple)):
            return len(candidate)
    if isinstance(value, (list, tuple)):
        return len(value)
    return 0

def require_nonempty(value: Any, label: str) -> None:
    if value is None:
        raise RuntimeError(f"{label} returned no response")

async def main() -> int:
    missing = [name for name in REQUIRED if not os.getenv(name)]
    if missing:
        print(json.dumps({"status":"BLOCKED_MISSING_CONFIGURATION",
                          "missing_names_only":missing,
                          "secret_values_exposed":False}, sort_keys=True))
        return 2
    if os.getenv("PARADOX_CDP_WALLET_READ_ONLY", "").lower() != "true":
        raise RuntimeError("CDP read-only safety flag must be true")
    if os.getenv("PARADOX_ADVANCED_TRADE_READ_ONLY", "").lower() != "true":
        raise RuntimeError("Advanced Trade read-only safety flag must be true")

    address = os.environ["PARADOX_CDP_EVM_ADDRESS"]
    network = os.environ["PARADOX_CDP_EVM_NETWORK"]
    product_id = os.getenv("PARADOX_COINBASE_PRODUCT_ID", "BTC-USD")
    if not address.startswith("0x") or len(address) != 42:
        raise RuntimeError("Configured EVM address has invalid shape")
    if network not in {"base","base-sepolia","ethereum","ethereum-sepolia","polygon","arbitrum","optimism"}:
        raise RuntimeError("Network is not in the explicitly supported read-only allowlist")
    if not product_id or len(product_id) > 32 or "-" not in product_id:
        raise RuntimeError("Product ID is invalid")

    # No wallet secret is loaded: no signing operation is performed.
    async with CdpClient(
        api_key_id=os.environ["CDP_API_KEY_ID"],
        api_key_secret=os.environ["CDP_API_KEY_SECRET"],
    ) as cdp:
        wallet = CDPWalletV2ReadOnly(client=cdp, enabled=True)
        balances = await wallet.list_evm_token_balances(address=address, network=network)
        require_nonempty(balances, "CDP token-balance read")
        balance_count = count_items(balances, "balances", "token_balances")

    trade = AdvancedTradeReadOnly(enabled=True)
    accounts = trade.list_accounts()
    require_nonempty(accounts, "Advanced Trade accounts read")
    products = trade.list_products(product_ids=[product_id])
    require_nonempty(products, "Advanced Trade product read")
    product = trade.get_product(product_id)
    require_nonempty(product, "Advanced Trade single-product read")
    private_quote = trade.get_best_bid_ask([product_id])
    require_nonempty(private_quote, "Advanced Trade authenticated quote read")
    public_book = trade.get_public_product_book(product_id)
    require_nonempty(public_book, "Advanced Trade public order-book read")

    report = {
        "schema":"PARADOX-COINBASE-READONLY-LIVE-CHECK-v1",
        "status":"PASS",
        "checked_at":datetime.now(timezone.utc).isoformat(),
        "wallet":{
            "status":"PASS","network":network,
            "address_sha256_prefix":hashlib.sha256(address.lower().encode()).hexdigest()[:16],
            "balance_items_returned":balance_count,
        },
        "advanced_trade":{
            "status":"PASS",
            "account_items_returned":count_items(accounts,"accounts"),
            "product_id":product_id,
            "product_items_returned":count_items(products,"products"),
            "single_product_read":"PASS",
            "authenticated_best_bid_ask_read":"PASS",
            "public_product_book_read":"PASS",
            "public_endpoint_parity":"BOTH_ENDPOINTS_RESPONDED",
        },
        "safety":{
            "wallet_signing":False,"wallet_creation":False,"faucet":False,
            "transaction_submission":False,"orders":False,"transfers":False,
            "withdrawals":False,"swaps":False,"raw_api_payloads_logged":False,
            "credentials_logged":False,
        },
    }
    print(json.dumps(report,sort_keys=True))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error_class":type(exc).__name__,
                          "error_details_suppressed":True,
                          "credentials_exposed":False},sort_keys=True))
        raise SystemExit(1)
