from enum import Enum
from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    MUTUAL_FUND = "mutual_fund"
    COMMODITY = "commodity"

class StockMetadata(BaseModel):
    market_cap: float = Field(..., description="Market capitalization in USD")
    sector: str
    industry: str
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: float
    fifty_two_week_low: float
    volume_24h: float

class CryptoMetadata(BaseModel):
    market_cap: float
    volume_24h: float
    circulating_supply: float
    total_supply: Optional[float] = None
    btc_dominance_percent: Optional[float] = None

class MutualFundMetadata(BaseModel):
    nav: float = Field(..., description="Net Asset Value")
    nav_change_24h: float
    aum: float = Field(..., description="Assets Under Management in USD")
    expense_ratio: float = Field(..., description="Expense ratio percentage, e.g. 0.15")
    fund_manager: str
    category: str
    benchmark: str
    risk_level: str  # e.g., "Low", "Moderate", "High"
    equity_allocation_pct: float
    debt_allocation_pct: float
    cash_allocation_pct: float

class CommodityMetadata(BaseModel):
    unit: str  # e.g., "USD/troy ounce", "USD/barrel", "USD/MMBtu"
    contract_type: str  # e.g., "Spot", "Futures"
    contract_month: Optional[str] = None
    volume_24h: float
    open_interest: Optional[float] = None

class BaseAsset(BaseModel):
    symbol: str
    name: str
    asset_type: AssetType
    currency: str = "USD"
    unit: str = "USD/share"  # e.g., USD/share, USD/token, USD/NAV, USD/troy oz
    current_price: float
    change_24h: float
    change_24h_pct: float
    sparkline_7d: list[float] = []
    last_updated: str
    metadata: Dict[str, Any] = {}

class AssetListResponse(BaseModel):
    assets: list[BaseAsset]
    total: int
    asset_types: list[str] = ["stock", "crypto", "mutual_fund", "commodity"]
