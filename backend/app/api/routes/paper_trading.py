from fastapi import APIRouter
from app.schemas.paper_trading import PortfolioState, TradeOrderRequest
from app.providers.mock.paper_trading import MockPaperTradingProvider

router = APIRouter(prefix="/paper-trading", tags=["Paper Trading"])
paper_trading_provider = MockPaperTradingProvider()

@router.get("/portfolio", response_model=PortfolioState)
def get_portfolio():
    return paper_trading_provider.get_portfolio()

@router.post("/trade", response_model=PortfolioState)
def execute_trade(trade: TradeOrderRequest):
    return paper_trading_provider.execute_trade(trade)

@router.post("/reset", response_model=PortfolioState)
def reset_portfolio():
    return paper_trading_provider.reset_portfolio()
