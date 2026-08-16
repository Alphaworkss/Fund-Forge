from app.providers.base import BaseNewsProvider
from app.providers.mock.assets import MOCK_ASSETS_DATABASE
from app.schemas.news import NewsResponse, NewsItem

class MockNewsProvider(BaseNewsProvider):
    def get_news(self, symbol: str) -> NewsResponse:
        asset = MOCK_ASSETS_DATABASE.get(symbol.upper())
        asset_type = asset.asset_type if asset else "crypto"

        items = [
            NewsItem(
                id="news-1",
                title=f"{symbol.upper()} Market Sentiment Strengthens as Institutional Inflows Increase",
                summary=f"Analytic models report positive momentum for {symbol.upper()} supported by strong market liquidity and institutional interest.",
                source="SarmayaSaaz Market Feed",
                timestamp="10 mins ago",
                sentiment="positive",
                asset_symbol=symbol.upper(),
                asset_type=asset_type,
                url=f"https://finance.yahoo.com/quote/{symbol.upper()}" if asset_type in ["stock", "crypto"] else "https://finance.yahoo.com"
            ),
            NewsItem(
                id="news-2",
                title=f"Macro Economic Report Highlights Key Factors Influencing {asset_type.replace('_', ' ').capitalize()} Assets",
                summary="Global rate expectations and liquidity conditions remain primary macroeconomic drivers.",
                source="Global Financial Digest",
                timestamp="1 hour ago",
                sentiment="neutral",
                asset_symbol=symbol.upper(),
                asset_type=asset_type,
                url="https://www.bloomberg.com/markets"
            ),
            NewsItem(
                id="news-3",
                title=f"AI Forecast Model Predicts High-Confidence Horizon for {symbol.upper()}",
                summary=f"PatchTST and XGBoost model ensembles highlight key support levels and projected target ranges for {symbol.upper()}.",
                source="SarmayaSaaz AI Research",
                timestamp="3 hours ago",
                sentiment="positive",
                asset_symbol=symbol.upper(),
                asset_type=asset_type,
                url="https://www.reuters.com/business/finance/"
            )
        ]

        return NewsResponse(
            symbol=symbol.upper(),
            news=items
        )
