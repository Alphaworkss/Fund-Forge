from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.assets import BaseAsset, AssetListResponse
from app.providers.mock.assets import MockAssetProvider

router = APIRouter(prefix="/assets", tags=["Assets"])
asset_provider = MockAssetProvider()

@router.get("", response_model=AssetListResponse)
def get_assets(type: Optional[str] = Query(None, description="Asset class filter: stock, crypto, mutual_fund, commodity")):
    return asset_provider.get_assets(asset_type=type)

@router.get("/{symbol}", response_model=BaseAsset)
def get_asset_by_symbol(symbol: str):
    asset = asset_provider.get_asset(symbol)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{symbol}' not found")
    return asset
