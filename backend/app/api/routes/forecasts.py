from fastapi import APIRouter, Query
from typing import Optional
from app.schemas.forecasts import ForecastResponse, AllForecastsResponse, TopMoversResponse
from app.providers.mock.forecasts import MockForecastProvider

router = APIRouter(prefix="/forecast", tags=["Forecasts"])
forecast_provider = MockForecastProvider()

@router.get("/top-movers", response_model=TopMoversResponse)
def get_top_movers(
    horizon: str = Query("30d", description="Forecast horizon: 1d, 7d, 14d, 30d, 90d"),
    type: Optional[str] = Query(None, description="Asset class filter: crypto, stock, mutual_fund, commodity")
):
    return forecast_provider.get_top_movers(horizon=horizon, asset_type=type)

@router.get("/{symbol}", response_model=ForecastResponse)
def get_forecast(symbol: str, horizon: str = Query("30d", description="Forecast horizon: 1d, 7d, 14d, 30d, 90d")):
    return forecast_provider.get_forecast(symbol=symbol, horizon=horizon)

@router.get("/{symbol}/all", response_model=AllForecastsResponse)
def get_all_forecasts(symbol: str):
    return forecast_provider.get_all_forecasts(symbol=symbol)

