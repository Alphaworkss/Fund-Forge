from pydantic import BaseModel
from typing import List

class NewsItem(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    timestamp: str
    sentiment: str  # positive, neutral, negative
    asset_symbol: str
    asset_type: str
    url: str = "#"

class NewsResponse(BaseModel):
    symbol: str
    news: List[NewsItem]
