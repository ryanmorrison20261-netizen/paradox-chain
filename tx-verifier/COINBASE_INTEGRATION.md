# Coinbase dual integration (read-only by default)

## Components
- `tools/cdp_wallet_v2_adapter.py`: official CDP Python SDK adapter exposing only EVM token-balance reads.
- `tools/advanced_trade_readonly.py`: official Advanced Trade Python SDK adapter exposing account/product/quote reads only.
- `tools/der_multiauth.py`: application-level DER/secp256k1 M-of-N request authorization. This is separate from Coinbase JWT authentication.

## Install
```bash
pip install cdp-sdk coinbase-advanced-py
```

## Wallet API v2
Set `PARADOX_CDP_WALLET_READ_ONLY=true` to instantiate the adapter. CDP credentials are loaded by the official SDK from its supported environment variables (`CDP_API_KEY_ID`, `CDP_API_KEY_SECRET`, and wallet secret only when required by a selected operation). The implemented balance read is:
```python
from cdp_wallet_v2_adapter import CDPWalletV2ReadOnly
adapter = CDPWalletV2ReadOnly()
balances = await adapter.list_evm_token_balances(address="0x...", network="base-sepolia")
```
No wallet creation, private-key export, signing, faucet, transfer, swap, or transaction send method is exposed.

## Advanced Trade
Create a dedicated CDP API key with **View** permission only and an IP allowlist. Set:
- `PARADOX_ADVANCED_TRADE_READ_ONLY=true`
- `COINBASE_ADVANCED_API_KEY`
- `COINBASE_ADVANCED_API_SECRET`

Example:
```python
from advanced_trade_readonly import AdvancedTradeReadOnly
api = AdvancedTradeReadOnly()
accounts = api.list_accounts()
products = api.list_products()
```
The adapter only exposes GET/read SDK calls. It does not expose order creation, cancellation, transfers, or withdrawals.

## Safety invariants
- Both adapters are disabled by default.
- Use separate CDP credentials per product and least-privilege permissions.
- The Advanced Trade key must be View-only. Do not supply Trade or Transfer permissions.
- No live financial operation is enabled by this integration.
- DER multi-auth is an application authorization layer, not a substitute for Coinbase's own API-key JWT authentication.
- The in-memory nonce guard in the initial DER module is for single-process tests only; production deployment must use an atomic shared nonce store.
- Wallet API balance reads are not guaranteed to be testnet-only. The adapter is read-only and must still be used with credentials and network selection appropriate to the environment.

## Verification status
Unit tests use mocks and verify safety gates and adapter call wiring. They do not establish connectivity to Coinbase. Live/sandbox credential validation remains pending until credentials are provisioned by the account owner. Never place API secrets in source control or chat.
