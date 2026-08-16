from fastapi import APIRouter
from app.schemas.features import FeatureImportanceResponse
from app.providers.mock.features import MockFeatureProvider

router = APIRouter(prefix="/features", tags=["Features"])
feature_provider = MockFeatureProvider()

@router.get("/{symbol}", response_model=FeatureImportanceResponse)
def get_features(symbol: str):
    return feature_provider.get_features(symbol=symbol)
