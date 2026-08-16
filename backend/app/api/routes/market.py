from fastapi import APIRouter, Query
from typing import Optional
from app.schemas.market import MarketOverviewResponse
from app.providers.mock.market import MockMarketProvider

router = APIRouter(prefix="/market", tags=["Market"])
market_provider = MockMarketProvider()

@router.get("/overview", response_model=MarketOverviewResponse)
def get_market_overview(type: Optional[str] = Query(None, description="Filter overview by asset type")):
    return market_provider.get_market_overview(asset_type=type)
