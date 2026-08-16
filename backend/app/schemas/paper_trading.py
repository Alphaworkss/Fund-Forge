from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TradeOrderRequest(BaseModel):
    symbol: str
    action: str  # buy, sell
    quantity: float

class PositionHolding(BaseModel):
    symbol: str
    name: str
    asset_type: str
    quantity: float
    avg_buy_price: float
    current_price: float
    current_market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float

class TradeTransaction(BaseModel):
    id: str
    timestamp: str
    symbol: str
    asset_type: str
    action: str
    quantity: float
    execution_price: float
    total_cost: float

class PortfolioState(BaseModel):
    starting_balance: float = 100000.0
    cash_balance: float
    holdings_value: float
    total_portfolio_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float
    realized_pnl_pct: float
    total_return_pct: float
    holdings: List[PositionHolding]
    recent_transactions: List[TradeTransaction]
    asset_allocation: Dict[str, float]  # e.g., {"stock": 40.0, "crypto": 30.0, "mutual_fund": 20.0, "commodity": 10.0}
