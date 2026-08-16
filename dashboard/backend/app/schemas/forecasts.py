from pydantic import BaseModel
from typing import List, Optional

class ForecastPoint(BaseModel):
    timestamp: str
    central_estimate: float
    lower_bound: float
    upper_bound: float

class ForecastResponse(BaseModel):
    symbol: str
    asset_type: str
    horizon: str  # 1d, 7d, 14d, 30d, 90d
    current_value: float
    lower_bound: float
    upper_bound: float
    central_estimate: float
    direction: str  # bullish, bearish, neutral
    confidence: float  # e.g., 0.82
    model: str  # PatchTST, TFT, LightGBM, XGBoost, ARIMA
    model_accuracy: float  # R2 or R-squared score
    mae: float
    rmse: float
    generated_at: str
    forecast_series: List[ForecastPoint] = []

class AllForecastsResponse(BaseModel):
    symbol: str
    asset_type: str
    forecasts: List[ForecastResponse]

class MoverItem(BaseModel):
    symbol: str
    name: str
    asset_type: str
    current_price: float
    predicted_target: float
    predicted_change_pct: float
    direction: str
    confidence: float
    model: str
    unit: str

class TopMoversResponse(BaseModel):
    horizon: str
    asset_type: Optional[str] = None
    gainers: List[MoverItem]
    losers: List[MoverItem]

