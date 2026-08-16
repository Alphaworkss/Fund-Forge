from pydantic import BaseModel
from typing import List

class PricePoint(BaseModel):
    timestamp: str
    price: float
    volume: float
    open: float
    high: float
    low: float
    close: float

class HistoryResponse(BaseModel):
    symbol: str
    asset_type: str
    period: str  # 1d, 7d, 14d, 30d, 90d, 1y
    unit: str
    points: List[PricePoint]
