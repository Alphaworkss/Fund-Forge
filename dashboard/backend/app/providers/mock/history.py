import math
from datetime import datetime, timedelta
from app.providers.base import BaseHistoryProvider
from app.providers.mock.assets import MOCK_ASSETS_DATABASE
from app.schemas.history import HistoryResponse, PricePoint

PERIOD_DAYS = {
    "1d": 1,
    "7d": 7,
    "14d": 14,
    "30d": 30,
    "90d": 90,
    "1y": 365
}

class MockHistoryProvider(BaseHistoryProvider):
    def get_history(self, symbol: str, period: str = "30d") -> HistoryResponse:
        asset = MOCK_ASSETS_DATABASE.get(symbol.upper())
        base_price = asset.current_price if asset else 100.0
        asset_type = asset.asset_type if asset else "crypto"
        unit = asset.unit if asset else "USD/share"

        days = PERIOD_DAYS.get(period.lower(), 30)
        num_points = 30 if days <= 30 else (60 if days <= 90 else 100)
        
        now = datetime.utcnow()
        points: list[PricePoint] = []

        # Seeded deterministic trend formula
        seed = sum(ord(c) for c in symbol.upper())
        
        for i in range(num_points):
            t_offset = days * (1.0 - i / (num_points - 1))
            dt = now - timedelta(days=t_offset)
            
            # Sine wave trend + noise
            phase = (i / num_points) * 4 * math.pi
            noise = math.sin(phase + seed) * 0.05 + math.cos(phase * 0.5) * 0.03
            price = base_price * (1 - (days - t_offset) * 0.001) * (1 + noise)
            
            high = price * 1.015
            low = price * 0.985
            open_p = price * (1.0 - (math.sin(i) * 0.005))
            close_p = price
            vol = base_price * 1000 * (1 + math.sin(i * 0.3) * 0.2)

            points.append(PricePoint(
                timestamp=dt.strftime("%Y-%m-%d %H:%M"),
                price=round(price, 2),
                volume=round(vol, 2),
                open=round(open_p, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close_p, 2)
            ))

        return HistoryResponse(
            symbol=symbol.upper(),
            asset_type=asset_type,
            period=period,
            unit=unit,
            points=points
        )
