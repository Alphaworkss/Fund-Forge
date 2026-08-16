from abc import ABC, abstractmethod
from typing import Optional, List
from app.schemas.assets import BaseAsset, AssetListResponse
from app.schemas.market import MarketOverviewResponse
from app.schemas.history import HistoryResponse
from app.schemas.forecasts import ForecastResponse, AllForecastsResponse
from app.schemas.models import ModelInfoResponse
from app.schemas.features import FeatureImportanceResponse
from app.schemas.news import NewsResponse
from app.schemas.paper_trading import PortfolioState, TradeOrderRequest

class BaseAssetProvider(ABC):
    @abstractmethod
    def get_assets(self, asset_type: Optional[str] = None) -> AssetListResponse:
        pass

    @abstractmethod
    def get_asset(self, symbol: str) -> Optional[BaseAsset]:
        pass

class BaseMarketProvider(ABC):
    @abstractmethod
    def get_market_overview(self, asset_type: Optional[str] = None) -> MarketOverviewResponse:
        pass

class BaseHistoryProvider(ABC):
    @abstractmethod
    def get_history(self, symbol: str, period: str = "30d") -> HistoryResponse:
        pass

class BaseForecastProvider(ABC):
    @abstractmethod
    def get_forecast(self, symbol: str, horizon: str = "30d") -> ForecastResponse:
        pass

    @abstractmethod
    def get_all_forecasts(self, symbol: str) -> AllForecastsResponse:
        pass

    @abstractmethod
    def get_top_movers(self, horizon: str = "30d", asset_type: Optional[str] = None) -> TopMoversResponse:
        pass

class BaseModelProvider(ABC):
    @abstractmethod
    def get_model_info(self, symbol: str) -> ModelInfoResponse:
        pass

class BaseFeatureProvider(ABC):
    @abstractmethod
    def get_features(self, symbol: str) -> FeatureImportanceResponse:
        pass

class BaseNewsProvider(ABC):
    @abstractmethod
    def get_news(self, symbol: str) -> NewsResponse:
        pass

class BasePaperTradingProvider(ABC):
    @abstractmethod
    def get_portfolio(self) -> PortfolioState:
        pass

    @abstractmethod
    def execute_trade(self, trade: TradeOrderRequest) -> PortfolioState:
        pass

    @abstractmethod
    def reset_portfolio(self) -> PortfolioState:
        pass
