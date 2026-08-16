from typing import Optional, Dict
from app.providers.base import BaseAssetProvider
from app.schemas.assets import BaseAsset, AssetListResponse, AssetType

MOCK_ASSETS_DATABASE: Dict[str, BaseAsset] = {
    # Cryptocurrencies
    "BTC": BaseAsset(
        symbol="BTC",
        name="Bitcoin",
        asset_type=AssetType.CRYPTO,
        currency="USD",
        unit="USD/token",
        current_price=118420.50,
        change_24h=3840.20,
        change_24h_pct=3.35,
        sparkline_7d=[112000, 114500, 113200, 115800, 117000, 116500, 118420.50],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "market_cap": 2340500000000.0,
            "volume_24h": 48500000000.0,
            "circulating_supply": 19750000.0,
            "total_supply": 21000000.0,
            "btc_dominance_percent": 56.4
        }
    ),
    "ETH": BaseAsset(
        symbol="ETH",
        name="Ethereum",
        asset_type=AssetType.CRYPTO,
        currency="USD",
        unit="USD/token",
        current_price=3850.75,
        change_24h=142.10,
        change_24h_pct=3.83,
        sparkline_7d=[3600, 3650, 3700, 3680, 3750, 3800, 3850.75],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "market_cap": 462000000000.0,
            "volume_24h": 22100000000.0,
            "circulating_supply": 120200000.0,
            "total_supply": 120200000.0
        }
    ),
    "SOL": BaseAsset(
        symbol="SOL",
        name="Solana",
        asset_type=AssetType.CRYPTO,
        currency="USD",
        unit="USD/token",
        current_price=185.30,
        change_24h=-2.40,
        change_24h_pct=-1.28,
        sparkline_7d=[192, 190, 188, 186, 189, 187, 185.30],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "market_cap": 86500000000.0,
            "volume_24h": 4200000000.0,
            "circulating_supply": 466000000.0
        }
    ),
    "BNB": BaseAsset(
        symbol="BNB",
        name="BNB",
        asset_type=AssetType.CRYPTO,
        currency="USD",
        unit="USD/token",
        current_price=580.40,
        change_24h=12.50,
        change_24h_pct=2.20,
        sparkline_7d=[560, 565, 570, 572, 575, 578, 580.40],
        last_updated="2026-08-12T10:45:00Z",
        metadata={"market_cap": 85000000000.0, "volume_24h": 1200000000.0, "circulating_supply": 147000000.0}
    ),
    "XRP": BaseAsset(
        symbol="XRP",
        name="XRP",
        asset_type=AssetType.CRYPTO,
        currency="USD",
        unit="USD/token",
        current_price=0.62,
        change_24h=0.03,
        change_24h_pct=5.08,
        sparkline_7d=[0.58, 0.59, 0.60, 0.59, 0.61, 0.61, 0.62],
        last_updated="2026-08-12T10:45:00Z",
        metadata={"market_cap": 34800000000.0, "volume_24h": 1800000000.0, "circulating_supply": 56000000000.0}
    ),

    # Stocks
    "AAPL": BaseAsset(
        symbol="AAPL",
        name="Apple Inc.",
        asset_type=AssetType.STOCK,
        currency="USD",
        unit="USD/share",
        current_price=224.50,
        change_24h=3.80,
        change_24h_pct=1.72,
        sparkline_7d=[218, 220, 219, 221, 223, 222, 224.50],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "market_cap": 3450000000000.0,
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "pe_ratio": 33.4,
            "eps": 6.72,
            "dividend_yield": 0.44,
            "fifty_two_week_high": 237.23,
            "fifty_two_week_low": 164.08,
            "volume_24h": 48200000.0
        }
    ),
    "NVDA": BaseAsset(
        symbol="NVDA",
        name="NVIDIA Corporation",
        asset_type=AssetType.STOCK,
        currency="USD",
        unit="USD/share",
        current_price=128.90,
        change_24h=5.40,
        change_24h_pct=4.37,
        sparkline_7d=[118, 120, 122, 121, 125, 126, 128.90],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "market_cap": 3170000000000.0,
            "sector": "Technology",
            "industry": "Semiconductors",
            "pe_ratio": 64.2,
            "eps": 2.01,
            "dividend_yield": 0.03,
            "fifty_two_week_high": 140.76,
            "fifty_two_week_low": 45.01,
            "volume_24h": 72500000.0
        }
    ),
    "MSFT": BaseAsset(
        symbol="MSFT",
        name="Microsoft Corporation",
        asset_type=AssetType.STOCK,
        currency="USD",
        unit="USD/share",
        current_price=448.20,
        change_24h=2.10,
        change_24h_pct=0.47,
        sparkline_7d=[440, 442, 445, 443, 446, 447, 448.20],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "market_cap": 3330000000000.0,
            "sector": "Technology",
            "industry": "Software—Infrastructure",
            "pe_ratio": 37.8,
            "eps": 11.85,
            "dividend_yield": 0.67,
            "fifty_two_week_high": 468.35,
            "fifty_two_week_low": 309.45,
            "volume_24h": 21000000.0
        }
    ),
    "AMZN": BaseAsset(
        symbol="AMZN",
        name="Amazon.com Inc.",
        asset_type=AssetType.STOCK,
        currency="USD",
        unit="USD/share",
        current_price=186.40,
        change_24h=-1.20,
        change_24h_pct=-0.64,
        sparkline_7d=[189, 188, 187, 188, 186, 187, 186.40],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "market_cap": 1940000000000.0,
            "sector": "Consumer Cyclical",
            "industry": "Internet Retail",
            "pe_ratio": 42.1,
            "eps": 4.43,
            "dividend_yield": 0.0,
            "fifty_two_week_high": 201.20,
            "fifty_two_week_low": 118.35,
            "volume_24h": 38000000.0
        }
    ),

    # Mutual Funds
    "GROWTH_FUND": BaseAsset(
        symbol="GROWTH_FUND",
        name="SarmayaSaaz Global Tech Growth Fund",
        asset_type=AssetType.MUTUAL_FUND,
        currency="USD",
        unit="USD/NAV",
        current_price=54.80,
        change_24h=0.65,
        change_24h_pct=1.20,
        sparkline_7d=[53.2, 53.5, 53.8, 54.0, 54.2, 54.5, 54.80],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "nav": 54.80,
            "nav_change_24h": 0.65,
            "aum": 4850000000.0,
            "expense_ratio": 0.45,
            "fund_manager": "Sarah Jenkins, CFA",
            "category": "Equity Tech Growth",
            "benchmark": "S&P 500 Information Technology Index",
            "risk_level": "High",
            "equity_allocation_pct": 88.5,
            "debt_allocation_pct": 5.0,
            "cash_allocation_pct": 6.5
        }
    ),
    "INCOME_FUND": BaseAsset(
        symbol="INCOME_FUND",
        name="SarmayaSaaz High Yield Bond & Income Fund",
        asset_type=AssetType.MUTUAL_FUND,
        currency="USD",
        unit="USD/NAV",
        current_price=28.15,
        change_24h=0.08,
        change_24h_pct=0.28,
        sparkline_7d=[27.95, 28.00, 28.05, 28.10, 28.12, 28.14, 28.15],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "nav": 28.15,
            "nav_change_24h": 0.08,
            "aum": 2100000000.0,
            "expense_ratio": 0.30,
            "fund_manager": "David Chen, CFA",
            "category": "Fixed Income Corporate Bond",
            "benchmark": "Bloomberg US Corporate High Yield Index",
            "risk_level": "Moderate",
            "equity_allocation_pct": 10.0,
            "debt_allocation_pct": 82.0,
            "cash_allocation_pct": 8.0
        }
    ),

    # Commodities
    "GOLD": BaseAsset(
        symbol="GOLD",
        name="Gold Spot",
        asset_type=AssetType.COMMODITY,
        currency="USD",
        unit="USD/troy ounce",
        current_price=2435.80,
        change_24h=18.40,
        change_24h_pct=0.76,
        sparkline_7d=[2390, 2405, 2410, 2420, 2415, 2428, 2435.80],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "unit": "USD/troy ounce",
            "contract_type": "Spot",
            "contract_month": "AUG 2026",
            "volume_24h": 14500000000.0,
            "open_interest": 485000.0
        }
    ),
    "CRUDE_OIL": BaseAsset(
        symbol="CRUDE_OIL",
        name="WTI Crude Oil",
        asset_type=AssetType.COMMODITY,
        currency="USD",
        unit="USD/barrel",
        current_price=78.45,
        change_24h=-1.15,
        change_24h_pct=-1.44,
        sparkline_7d=[81.0, 80.5, 79.8, 79.2, 79.5, 79.0, 78.45],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "unit": "USD/barrel",
            "contract_type": "Futures",
            "contract_month": "SEP 2026",
            "volume_24h": 22000000000.0,
            "open_interest": 320000.0
        }
    ),
    "NATURAL_GAS": BaseAsset(
        symbol="NATURAL_GAS",
        name="Natural Gas",
        asset_type=AssetType.COMMODITY,
        currency="USD",
        unit="USD/MMBtu",
        current_price=2.35,
        change_24h=0.08,
        change_24h_pct=3.52,
        sparkline_7d=[2.20, 2.22, 2.25, 2.28, 2.30, 2.32, 2.35],
        last_updated="2026-08-12T10:45:00Z",
        metadata={
            "unit": "USD/MMBtu",
            "contract_type": "Futures",
            "contract_month": "SEP 2026",
            "volume_24h": 5400000000.0,
            "open_interest": 120000.0
        }
    )
}

class MockAssetProvider(BaseAssetProvider):
    def get_assets(self, asset_type: Optional[str] = None) -> AssetListResponse:
        assets_list = list(MOCK_ASSETS_DATABASE.values())
        if asset_type:
            assets_list = [a for a in assets_list if a.asset_type == asset_type]
        return AssetListResponse(
            assets=assets_list,
            total=len(assets_list),
            asset_types=["stock", "crypto", "mutual_fund", "commodity"]
        )

    def get_asset(self, symbol: str) -> Optional[BaseAsset]:
        return MOCK_ASSETS_DATABASE.get(symbol.upper())
