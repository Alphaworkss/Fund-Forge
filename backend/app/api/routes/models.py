from fastapi import APIRouter
from app.schemas.models import ModelInfoResponse
from app.providers.mock.models import MockModelProvider

router = APIRouter(prefix="/model", tags=["Models"])
model_provider = MockModelProvider()

@router.get("/{symbol}", response_model=ModelInfoResponse)
def get_model_info(symbol: str):
    return model_provider.get_model_info(symbol=symbol)
