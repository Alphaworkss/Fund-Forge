from datetime import datetime, timedelta
import math
from app.providers.base import BaseForecastProvider
from app.providers.mock.assets import MOCK_ASSETS_DATABASE
from app.schemas.forecasts import ForecastResponse, AllForecastsResponse, ForecastPoint, TopMoversResponse, MoverItem

HORIZONS = ["1d", "7d", "14d", "30d", "90d"]

class MockForecastProvider(BaseForecastProvider):
    def get_forecast(self, symbol: str, horizon: str = "30d") -> ForecastResponse:
        asset = MOCK_ASSETS_DATABASE.get(symbol.upper())
        current_val = asset.current_price if asset else 100.0
        asset_type = asset.asset_type if asset else "crypto"

        # Horizon multipliers
        mult_map = {"1d": 0.015, "7d": 0.04, "14d": 0.06, "30d": 0.12, "90d": 0.25}
        pct_spread = mult_map.get(horizon.lower(), 0.10)

        seed = sum(ord(c) for c in symbol.upper())
        direction = "bullish" if seed % 2 == 0 else "neutral"

        central = current_val * (1.06 if direction == "bullish" else 1.01)
        lower = central * (1 - pct_spread)
        upper = central * (1 + pct_spread)

        # Generated forecast points
        now = datetime.utcnow()
        days_map = {"1d": 1, "7d": 7, "14d": 14, "30d": 30, "90d": 90, "1y": 365, "365d": 365}
        days_num = days_map.get(horizon.lower(), 30)
        points: list[ForecastPoint] = []
        for i in range(1, 11):
            dt = now + timedelta(days=(days_num * i / 10.0))
            frac = i / 10.0
            p_central = current_val + (central - current_val) * frac
            p_lower = current_val + (lower - current_val) * frac
            p_upper = current_val + (upper - current_val) * frac
            points.append(ForecastPoint(
                timestamp=dt.strftime("%Y-%m-%d"),
                central_estimate=round(p_central, 2),
                lower_bound=round(p_lower, 2),
                upper_bound=round(p_upper, 2)
            ))

        return ForecastResponse(
            symbol=symbol.upper(),
            asset_type=asset_type,
            horizon=horizon,
            current_value=current_val,
            lower_bound=round(lower, 2),
            upper_bound=round(upper, 2),
            central_estimate=round(central, 2),
            direction=direction,
            confidence=0.84 if horizon in ["1d", "7d"] else 0.76,
            model="PatchTST" if asset_type == "crypto" else ("XGBoost" if asset_type == "stock" else "LightGBM"),
            model_accuracy=0.874,
            mae=round(current_val * 0.018, 2),
            rmse=round(current_val * 0.024, 2),
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            forecast_series=points
        )

    def get_all_forecasts(self, symbol: str) -> AllForecastsResponse:
        asset = MOCK_ASSETS_DATABASE.get(symbol.upper())
        asset_type = asset.asset_type if asset else "crypto"
        return AllForecastsResponse(
            symbol=symbol.upper(),
            asset_type=asset_type,
            forecasts=[self.get_forecast(symbol, h) for h in HORIZONS]
        )

    def get_top_movers(self, horizon: str = "30d", asset_type: Optional[str] = None) -> TopMoversResponse:
        assets_list = list(MOCK_ASSETS_DATABASE.values())
        if asset_type and asset_type.lower() != "all":
            assets_list = [a for a in assets_list if a.asset_type == asset_type.lower()]

        items: list[MoverItem] = []
        for asset in assets_list:
            fc = self.get_forecast(asset.symbol, horizon)
            pct_change = round(((fc.central_estimate - fc.current_value) / fc.current_value) * 100.0, 2)
            
            # Add algorithmic variation to gainers vs losers based on symbol hash
            h_code = sum(ord(c) for c in asset.symbol)
            if h_code % 3 == 0:
                # Bearish simulated mover
                pct_change = -abs(pct_change * 0.8)
                fc.direction = "bearish"
                fc.central_estimate = round(asset.current_price * (1 + pct_change / 100.0), 2)

            items.append(MoverItem(
                symbol=asset.symbol,
                name=asset.name,
                asset_type=asset.asset_type,
                current_price=asset.current_price,
                predicted_target=fc.central_estimate,
                predicted_change_pct=pct_change,
                direction=fc.direction,
                confidence=fc.confidence,
                model=fc.model,
                unit=asset.unit
            ))

        # Sort gainers and losers
        gainers = sorted([i for i in items if i.predicted_change_pct >= 0], key=lambda x: x.predicted_change_pct, reverse=True)[:10]
        losers = sorted([i for i in items if i.predicted_change_pct < 0], key=lambda x: x.predicted_change_pct)[:10]

        # If gainers or losers list is empty, populate fallback items so user always sees top 10 gainers & losers
        if not gainers:
            gainers = sorted(items, key=lambda x: x.predicted_change_pct, reverse=True)[:10]
        if not losers:
            losers = sorted(items, key=lambda x: x.predicted_change_pct)[:10]

        return TopMoversResponse(
            horizon=horizon,
            asset_type=asset_type,
            gainers=gainers,
            losers=losers
        )

