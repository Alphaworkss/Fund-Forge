from typing import Optional
from app.providers.base import BaseMarketProvider
from app.providers.mock.assets import MOCK_ASSETS_DATABASE
from app.schemas.market import MarketOverviewResponse, MarketOverviewStats

class MockMarketProvider(BaseMarketProvider):
    def get_market_overview(self, asset_type: Optional[str] = None) -> MarketOverviewResponse:
        all_assets = list(MOCK_ASSETS_DATABASE.values())
        if asset_type:
            all_assets = [a for a in all_assets if a.asset_type == asset_type]

        sorted_by_change = sorted(all_assets, key=lambda a: a.change_24h_pct, reverse=True)
        top_gainers = sorted_by_change[:3]
        top_losers = sorted_by_change[-3:][::-1]

        btc_asset = MOCK_ASSETS_DATABASE.get("BTC", all_assets[0])

        return MarketOverviewResponse(
            stats=MarketOverviewStats(
                total_market_cap=2780000000000.0,
                market_cap_change_24h_pct=2.45,
                volume_24h=94500000000.0,
                btc_dominance=56.4,
                fear_and_greed_index=68,
                fear_and_greed_label="Greed"
            ),
            top_gainers=top_gainers,
            top_losers=top_losers,
            trending_assets=all_assets[:4],
            featured_asset=btc_asset
        )
