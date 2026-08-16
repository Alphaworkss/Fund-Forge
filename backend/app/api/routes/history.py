from fastapi import APIRouter, Query
from app.schemas.history import HistoryResponse
from app.providers.mock.history import MockHistoryProvider

router = APIRouter(prefix="/history", tags=["History"])
history_provider = MockHistoryProvider()

@router.get("/{symbol}", response_model=HistoryResponse)
def get_history(symbol: str, period: str = Query("30d", description="Period horizon: 1d, 7d, 14d, 30d, 90d, 1y")):
    return history_provider.get_history(symbol=symbol, period=period)
