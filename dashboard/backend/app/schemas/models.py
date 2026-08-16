from pydantic import BaseModel
from typing import List

class ModelMetric(BaseModel):
    name: str  # PatchTST, TFT, LightGBM, XGBoost, ARIMA
    architecture: str
    r2_score: float
    mae: float
    rmse: float
    mape_pct: float
    is_winning_model: bool
    training_period: str

class ModelInfoResponse(BaseModel):
    symbol: str
    asset_type: str
    selected_model: str
    winning_metric: ModelMetric
    candidate_models: List[ModelMetric]
    last_trained: str
