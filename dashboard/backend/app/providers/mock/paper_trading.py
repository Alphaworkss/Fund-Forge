from datetime import datetime
from typing import Dict, List
from app.providers.base import BasePaperTradingProvider
from app.providers.mock.assets import MOCK_ASSETS_DATABASE
from app.schemas.paper_trading import PortfolioState, PositionHolding, TradeTransaction, TradeOrderRequest

class MockPaperTradingProvider(BasePaperTradingProvider):
    def __init__(self):
        self._reset()

    def _reset(self):
        self.starting_balance = 100000.0
        self.cash_balance = 100000.0
        self.holdings_map: Dict[str, PositionHolding] = {}
        self.transactions: List[TradeTransaction] = []
        self.realized_pnl = 0.0

    def get_portfolio(self) -> PortfolioState:
        # Update current market prices for holdings
        total_holdings_val = 0.0
        total_unrealized_pnl = 0.0
        asset_alloc: Dict[str, float] = {}

        for sym, holding in self.holdings_map.items():
            asset_info = MOCK_ASSETS_DATABASE.get(sym)
            if asset_info:
                holding.current_price = asset_info.current_price
            holding.current_market_value = holding.quantity * holding.current_price
            cost_basis = holding.quantity * holding.avg_buy_price
            holding.unrealized_pnl = holding.current_market_value - cost_basis
            holding.unrealized_pnl_pct = (holding.unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0

            total_holdings_val += holding.current_market_value
            total_unrealized_pnl += holding.unrealized_pnl
            
            atype = holding.asset_type
            asset_alloc[atype] = asset_alloc.get(atype, 0.0) + holding.current_market_value

        total_portfolio_val = self.cash_balance + total_holdings_val
        total_pnl = total_unrealized_pnl + self.realized_pnl
        total_return_pct = (total_pnl / self.starting_balance) * 100.0

        # Percentages for allocation
        if total_holdings_val > 0:
            asset_alloc_pct = {k: round((v / total_holdings_val) * 100, 1) for k, v in asset_alloc.items()}
        else:
            asset_alloc_pct = {"cash": 100.0}

        return PortfolioState(
            starting_balance=self.starting_balance,
            cash_balance=round(self.cash_balance, 2),
            holdings_value=round(total_holdings_val, 2),
            total_portfolio_value=round(total_portfolio_val, 2),
            unrealized_pnl=round(total_unrealized_pnl, 2),
            unrealized_pnl_pct=round((total_unrealized_pnl / (total_holdings_val if total_holdings_val > 0 else 1)) * 100, 2),
            realized_pnl=round(self.realized_pnl, 2),
            realized_pnl_pct=round((self.realized_pnl / self.starting_balance) * 100, 2),
            total_return_pct=round(total_return_pct, 2),
            holdings=list(self.holdings_map.values()),
            recent_transactions=self.transactions[::-1],
            asset_allocation=asset_alloc_pct
        )

    def execute_trade(self, trade: TradeOrderRequest) -> PortfolioState:
        sym = trade.symbol.upper()
        asset = MOCK_ASSETS_DATABASE.get(sym)
        price = asset.current_price if asset else 100.0
        atype = asset.asset_type if asset else "crypto"
        name = asset.name if asset else sym

        cost = trade.quantity * price
        action = trade.action.upper()

        if action == "BUY":
            if self.cash_balance < cost:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=f"Insufficient cash balance (${self.cash_balance:,.2f}) for trade order costing ${cost:,.2f}")
            self.cash_balance -= cost
            if sym in self.holdings_map:
                h = self.holdings_map[sym]
                total_qty = h.quantity + trade.quantity
                new_avg = ((h.quantity * h.avg_buy_price) + cost) / total_qty
                h.quantity = total_qty
                h.avg_buy_price = new_avg
            else:
                self.holdings_map[sym] = PositionHolding(
                    symbol=sym,
                    name=name,
                    asset_type=atype,
                    quantity=trade.quantity,
                    avg_buy_price=price,
                    current_price=price,
                    current_market_value=cost,
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0
                )
        elif action == "SELL":
            if sym not in self.holdings_map or self.holdings_map[sym].quantity < trade.quantity:
                available = self.holdings_map[sym].quantity if sym in self.holdings_map else 0
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=f"Insufficient holding for {sym}. Available: {available}, Requested to SELL: {trade.quantity}")

            h = self.holdings_map[sym]
            proceeds = cost
            self.cash_balance += proceeds
            realized = (price - h.avg_buy_price) * trade.quantity
            self.realized_pnl += realized

            h.quantity -= trade.quantity
            if h.quantity <= 0.0001:
                del self.holdings_map[sym]

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        tx_id = f"tx-{len(self.transactions) + 101}"
        self.transactions.append(TradeTransaction(
            id=tx_id,
            timestamp=now_str,
            symbol=sym,
            asset_type=atype,
            action=action,
            quantity=trade.quantity,
            execution_price=price,
            total_cost=round(cost, 2)
        ))

        return self.get_portfolio()

    def reset_portfolio(self) -> PortfolioState:
        self._reset()
        return self.get_portfolio()
