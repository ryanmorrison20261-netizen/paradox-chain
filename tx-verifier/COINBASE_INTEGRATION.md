# Coinbase dual integration — read-only

## Components
- `tools/cdp_wallet_v2_adapter.py`: official CDP Python SDK adapter exposing EVM token-balance reads only.
- `tools/advanced_trade_readonly.py`: official Advanced Trade Python SDK adapter exposing account/product/quote reads and an unauthenticated public product-book read.
- `tools/live_coinbase_readonly_check.py`: opt-in live smoke test. It emits only metadata and suppresses exception messages.
- `tools/der_multiauth.py`: application-level DER/secp256k1 M-of-N request authorization. This is separate from Coinbase JWT authentication.

## Install
```bash
pip install cdp-sdk coinbase-advanced-py
```

## Wallet API v2
The live check uses `CDP_API_KEY_ID` and `CDP_API_KEY_SECRET` to initialize the official `CdpClient`. It deliberately does not load a wallet secret because it does not sign. Configure:
- `PARADOX_CDP_WALLET_READ_ONLY=true`
- `PARADOX_CDP_EVM_ADDRESS`: an EVM address you are authorized to inspect
- `PARADOX_CDP_EVM_NETWORK`: one of the script's explicit network allowlist values

The read operation is:
```python
await cdp.evm.list_token_balances(address=address, network=network)
```
No wallet creation, private-key export, signing, faucet, transfer, swap, or transaction send method is exposed by the adapter.

## Advanced Trade
Create a dedicated CDP API key with **View** permission only and an IP allowlist. Configure:
- `PARADOX_ADVANCED_TRADE_READ_ONLY=true`
- `COINBASE_ADVANCED_API_KEY`
- `COINBASE_ADVANCED_API_SECRET`
- optional `PARADOX_COINBASE_PRODUCT_ID` (defaults to `BTC-USD`)

The adapter exposes authenticated account, product and best-bid/ask reads, plus the unauthenticated public product-book endpoint. The live check calls both authenticated quote and public order-book endpoints to confirm both paths respond. This is endpoint parity within Coinbase, not an independent market-data provider.

## Live GitHub Actions configuration
Add these GitHub Actions **Secrets** (never repository files or chat):
- `CDP_API_KEY_ID`
- `CDP_API_KEY_SECRET`
- `COINBASE_ADVANCED_API_KEY`
- `COINBASE_ADVANCED_API_SECRET`

Add these GitHub Actions **Variables**:
- `PARADOX_CDP_EVM_ADDRESS`
- `PARADOX_CDP_EVM_NETWORK`
- optional `PARADOX_COINBASE_PRODUCT_ID`

Workflow: `.github/workflows/coinbase-readonly-live.yml`.
- Mocked tests run on branch pushes and pull requests.
- Live checks run on a branch push only when wallet address/network variables are configured, or by manually dispatching the workflow with `run_live=true`.
- If required secrets are absent, the live check reports only the missing variable names and fails closed.
- CDP error and usage telemetry are disabled for this smoke test.
- Logs contain no wallet address, balances, account contents, raw API payloads or credentials.

## Reproduce locally
Set the environment variables above in a secure shell/secret manager, then:
```bash
cd tx-verifier
python -m pip install cdp-sdk coinbase-advanced-py
PARADOX_CDP_WALLET_READ_ONLY=true PARADOX_ADVANCED_TRADE_READ_ONLY=true \
  python tools/live_coinbase_readonly_check.py
```

## Safety invariants
- Both adapters are disabled by default.
- Use separate credentials and least-privilege permissions.
- Advanced Trade key must be View-only; never supply Trade or Transfer permissions.
- No live financial operation is enabled.
- The live script invokes only documented GET/read operations and never logs secrets or returned financial details.
- The in-memory nonce guard in the initial DER module is for single-process tests only; production deployment must use an atomic shared nonce store.

## Verification status
Mock tests establish adapter wiring and safety gates; they do not establish live connectivity. Live status is established only by a successful `coinbase-readonly-live.yml` run. Never place API secrets, wallet secrets or private keys in source control or chat.
