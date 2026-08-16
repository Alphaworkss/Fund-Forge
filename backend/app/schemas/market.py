from pydantic import BaseModel
from typing import List, Optional
from app.schemas.assets import BaseAsset, AssetType

class MarketOverviewStats(BaseModel):
    total_market_cap: float
    market_cap_change_24h_pct: float
    volume_24h: float
    btc_dominance: float
    fear_and_greed_index: int
    fear_and_greed_label: str

class MarketOverviewResponse(BaseModel):
    stats: MarketOverviewStats
    top_gainers: List[BaseAsset]
    top_losers: List[BaseAsset]
    trending_assets: List[BaseAsset]
    featured_asset: BaseAsset
