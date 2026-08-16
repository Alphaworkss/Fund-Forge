from pydantic import BaseModel
from typing import List

class FeatureFactor(BaseModel):
    name: str
    category: str  # Technical, Fundamental, On-Chain, Macro, Sentiment, Supply/Demand
    shap_value: float  # Positive = bullish contribution, negative = bearish contribution
    impact: str  # High, Medium, Low
    description: str

class FeatureImportanceResponse(BaseModel):
    symbol: str
    asset_type: str
    factors: List[FeatureFactor]
    summary: str
