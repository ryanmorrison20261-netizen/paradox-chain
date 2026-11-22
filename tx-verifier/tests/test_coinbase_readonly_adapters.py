import os, sys, unittest
from unittest.mock import Mock, AsyncMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from cdp_wallet_v2_adapter import CDPWalletV2ReadOnly, IntegrationDisabled as WalletDisabled
from advanced_trade_readonly import AdvancedTradeReadOnly, IntegrationDisabled as TradeDisabled

class CoinbaseReadOnlyTests(unittest.TestCase):
    def test_wallet_disabled_by_default(self):
        with self.assertRaises(WalletDisabled):
            CDPWalletV2ReadOnly(client=Mock(), enabled=False)

    def test_trade_disabled_by_default(self):
        with self.assertRaises(TradeDisabled):
            AdvancedTradeReadOnly(client=Mock(), enabled=False)

    def test_advanced_trade_only_read_methods(self):
        client=Mock()
        client.get_accounts.return_value={"accounts":[]}
        client.get_products.return_value={"products":[]}
        client.get_product.return_value={"product_id":"BTC-USD"}
        client.get_best_bid_ask.return_value={"pricebooks":[]}
        adapter=AdvancedTradeReadOnly(client=client, enabled=True)
        self.assertEqual(adapter.list_accounts(), {"accounts":[]})
        self.assertEqual(adapter.list_products(), {"products":[]})
        self.assertEqual(adapter.get_product("BTC-USD"), {"product_id":"BTC-USD"})
        self.assertEqual(adapter.get_best_bid_ask(["BTC-USD"]), {"pricebooks":[]})
        self.assertFalse(any(name in adapter.__class__.__dict__ for name in ("create_order","market_order_buy","withdraw","transfer")))

    def test_advanced_trade_rejects_empty_product(self):
        adapter=AdvancedTradeReadOnly(client=Mock(), enabled=True)
        with self.assertRaises(ValueError): adapter.get_product("")

    def test_wallet_balance_uses_read_method(self):
        async def run():
            client=Mock()
            client.evm=Mock()
            client.evm.list_token_balances=AsyncMock(return_value={"balances":[]})
            adapter=CDPWalletV2ReadOnly(client=client, enabled=True)
            result=await adapter.list_evm_token_balances(address="0xabc", network="base-sepolia")
            self.assertEqual(result, {"balances":[]})
            client.evm.list_token_balances.assert_awaited_once_with(address="0xabc", network="base-sepolia")
        import asyncio
        asyncio.run(run())

    def test_wallet_requires_address_and_network(self):
        async def run():
            adapter=CDPWalletV2ReadOnly(client=Mock(), enabled=True)
            with self.assertRaises(ValueError):
                await adapter.list_evm_token_balances(address="", network="base-sepolia")
        import asyncio
        asyncio.run(run())

if __name__ == "__main__": unittest.main()
