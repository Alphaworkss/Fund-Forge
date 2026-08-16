from app.providers.base import BaseModelProvider
from app.providers.mock.assets import MOCK_ASSETS_DATABASE
from app.schemas.models import ModelInfoResponse, ModelMetric

class MockModelProvider(BaseModelProvider):
    def get_model_info(self, symbol: str) -> ModelInfoResponse:
        asset = MOCK_ASSETS_DATABASE.get(symbol.upper())
        asset_type = asset.asset_type if asset else "crypto"
        curr_price = asset.current_price if asset else 100.0

        models = [
            ModelMetric(
                name="PatchTST",
                architecture="Patch Time Series Transformer",
                r2_score=0.884,
                mae=round(curr_price * 0.015, 2),
                rmse=round(curr_price * 0.021, 2),
                mape_pct=1.52,
                is_winning_model=True if asset_type == "crypto" else False,
                training_period="2021-01 to 2026-06"
            ),
            ModelMetric(
                name="TFT",
                architecture="Temporal Fusion Transformer",
                r2_score=0.862,
                mae=round(curr_price * 0.018, 2),
                rmse=round(curr_price * 0.024, 2),
                mape_pct=1.84,
                is_winning_model=False,
                training_period="2021-01 to 2026-06"
            ),
            ModelMetric(
                name="LightGBM",
                architecture="Gradient Boosted Decision Trees",
                r2_score=0.875,
                mae=round(curr_price * 0.016, 2),
                rmse=round(curr_price * 0.022, 2),
                mape_pct=1.65,
                is_winning_model=True if asset_type in ["mutual_fund", "commodity"] else False,
                training_period="2021-01 to 2026-06"
            ),
            ModelMetric(
                name="XGBoost",
                architecture="eXtreme Gradient Boosting",
                r2_score=0.879,
                mae=round(curr_price * 0.016, 2),
                rmse=round(curr_price * 0.022, 2),
                mape_pct=1.60,
                is_winning_model=True if asset_type == "stock" else False,
                training_period="2021-01 to 2026-06"
            ),
            ModelMetric(
                name="ARIMA",
                architecture="AutoRegressive Integrated Moving Average",
                r2_score=0.742,
                mae=round(curr_price * 0.035, 2),
                rmse=round(curr_price * 0.045, 2),
                mape_pct=3.60,
                is_winning_model=False,
                training_period="2021-01 to 2026-06"
            )
        ]

        winning = next(m for m in models if m.is_winning_model)

        return ModelInfoResponse(
            symbol=symbol.upper(),
            asset_type=asset_type,
            selected_model=winning.name,
            winning_metric=winning,
            candidate_models=models,
            last_trained="2026-08-01T00:00:00Z"
        )
