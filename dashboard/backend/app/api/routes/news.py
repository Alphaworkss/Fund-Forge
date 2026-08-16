from fastapi import APIRouter
from app.schemas.news import NewsResponse
from app.providers.mock.news import MockNewsProvider

router = APIRouter(prefix="/news", tags=["News"])
news_provider = MockNewsProvider()

@router.get("/{symbol}", response_model=NewsResponse)
def get_news(symbol: str):
    return news_provider.get_news(symbol=symbol)
