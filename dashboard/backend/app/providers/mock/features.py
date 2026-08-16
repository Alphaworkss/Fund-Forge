from app.providers.base import BaseFeatureProvider
from app.providers.mock.assets import MOCK_ASSETS_DATABASE
from app.schemas.features import FeatureImportanceResponse, FeatureFactor

class MockFeatureProvider(BaseFeatureProvider):
    def get_features(self, symbol: str) -> FeatureImportanceResponse:
        asset = MOCK_ASSETS_DATABASE.get(symbol.upper())
        asset_type = asset.asset_type if asset else "crypto"

        if asset_type == "stock":
            factors = [
                FeatureFactor(
                    name="Q2 Earnings Surprise (+4.2%)",
                    category="Fundamental",
                    shap_value=0.28,
                    impact="High",
                    description="Stronger than expected EPS performance boosting bullish forecast sentiment."
                ),
                FeatureFactor(
                    name="Sector Momentum (Tech +2.8%)",
                    category="Market",
                    shap_value=0.19,
                    impact="High",
                    description="Broad tech sector strength providing tailwinds for equity valuation."
                ),
                FeatureFactor(
                    name="RSI Momentum (62.4)",
                    category="Technical",
                    shap_value=0.14,
                    impact="Medium",
                    description="Healthy bullish technical momentum above 50 day moving average."
                ),
                FeatureFactor(
                    name="P/E Valuation Multiple (33.4x)",
                    category="Fundamental",
                    shap_value=-0.08,
                    impact="Low",
                    description="Slight valuation headwind compared to historical sector medians."
                )
            ]
            summary = "Bullish price target driven primarily by strong quarterly earnings beat and tech sector momentum."

        elif asset_type == "mutual_fund":
            factors = [
                FeatureFactor(
                    name="Underlying Tech Holding Performance",
                    category="Allocation",
                    shap_value=0.32,
                    impact="High",
                    description="Top 10 equity holdings in Apple, Nvidia, and Microsoft posted gains."
                ),
                FeatureFactor(
                    name="Expense Ratio Efficiency (0.45%)",
                    category="Fund Management",
                    shap_value=0.12,
                    impact="Medium",
                    description="Low drag from management fees compared to category average."
                ),
                FeatureFactor(
                    name="Interest Rate Expectations",
                    category="Macro",
                    shap_value=-0.05,
                    impact="Low",
                    description="Yield curve stabilization creating neutral backdrop for equity funds."
                )
            ]
            summary = "Positive NAV outlook supported by heavy allocation to high-performing large-cap tech equities."

        elif asset_type == "commodity":
            factors = [
                FeatureFactor(
                    name="Global Central Bank Reserve Purchases",
                    category="Supply/Demand",
                    shap_value=0.35,
                    impact="High",
                    description="Sustained institutional and sovereign gold accumulation."
                ),
                FeatureFactor(
                    name="USD Index Weakness (-0.8%)",
                    category="Macro",
                    shap_value=0.22,
                    impact="High",
                    description="Softer US dollar enhances purchasing power for international buyers."
                ),
                FeatureFactor(
                    name="Geopolitical Hedging Demand",
                    category="Sentiment",
                    shap_value=0.18,
                    impact="Medium",
                    description="Safe-haven inflows into precious metals."
                )
            ]
            summary = "Strong commodity forecast anchored by central bank buying and US Dollar index pullback."

        else:  # Crypto default
            factors = [
                FeatureFactor(
                    name="24h Institutional Spot Inflows",
                    category="Market",
                    shap_value=0.34,
                    impact="High",
                    description="Net positive ETF and exchange inflows driving order book buy pressure."
                ),
                FeatureFactor(
                    name="BTC Market Dominance (56.4%)",
                    category="On-Chain",
                    shap_value=0.25,
                    impact="High",
                    description="Strong Bitcoin market leadership signaling healthy market structure."
                ),
                FeatureFactor(
                    name="Network Active Addresses (+12.4%)",
                    category="On-Chain",
                    shap_value=0.16,
                    impact="Medium",
                    description="Increased wallet activity and transaction volume."
                ),
                FeatureFactor(
                    name="Futures Funding Rate (0.012%)",
                    category="Technical",
                    shap_value=0.09,
                    impact="Low",
                    description="Balanced perpetual swap leverage indicating sustainable upward trend."
                )
            ]
            summary = "Highly bullish AI forecast backed by net institutional spot inflows and strong on-chain network health."

        return FeatureImportanceResponse(
            symbol=symbol.upper(),
            asset_type=asset_type,
            factors=factors,
            summary=summary
        )
