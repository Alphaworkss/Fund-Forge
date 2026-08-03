import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from database import SessionLocal, Fund, FundNAV, MarketIndicator, NewsArticle

def get_engineered_features(db: Session):
    """
    Retrieves database records and calculates rolling financial features
    and target labels for Machine Learning training.
    """
    # 1. Load Funds and NAV history into a Pandas DataFrame
    navs_query = db.query(
        FundNAV.date,
        FundNAV.nav,
        Fund.id.label("fund_id"),
        Fund.name.label("fund_name"),
        Fund.category.label("fund_category"),
        Fund.risk_level.label("fund_risk_level"),
        Fund.is_islamic.label("fund_is_islamic")
    ).join(Fund, FundNAV.fund_id == Fund.id).all()
    
    if not navs_query:
        print("No NAV history found in database. Run scraper first.")
        return pd.DataFrame()
        
    df_navs = pd.DataFrame(navs_query)
    # Ensure dates are in datetime format for sorting and math
    df_navs['date'] = pd.to_datetime(df_navs['date'])
    df_navs = df_navs.sort_values(by=["fund_id", "date"])
    
    # 2. Calculate rolling features for each fund
    # We group by fund_id to ensure we don't mix prices of different funds
    processed_funds = []
    for fund_id, group in df_navs.groupby("fund_id"):
        group = group.copy()
        
        # Calculate daily returns: (NAV_today - NAV_yesterday) / NAV_yesterday
        group['daily_return'] = group['nav'].pct_change()
        
        # Clue 1: Return over the last 7 days
        group['return_7d'] = group['nav'].pct_change(periods=7)
        
        # Clue 2: Return over the last 30 days
        group['return_30d'] = group['nav'].pct_change(periods=30)
        
        # Clue 3: Volatility (risk) - standard deviation of daily returns over last 30 days
        # We multiply by sqrt(252) to annualize the daily volatility, which is standard in finance
        group['volatility_30d'] = group['daily_return'].rolling(window=30).std() * np.sqrt(252)
        
        # Clue 4: Trend - current price relative to its 30-day average
        group['moving_avg_30d'] = group['nav'].rolling(window=30).mean()
        group['trend_30d'] = group['nav'] / group['moving_avg_30d']
        
        # Clue 5: TARGET (y) - The return of the fund over the NEXT 30 days
        # We shift the price back by 30 days: (NAV_30_days_in_future - NAV_today) / NAV_today
        group['target_return_30d'] = group['nav'].pct_change(periods=-30) * -1
        
        processed_funds.append(group)
        
    df_features = pd.concat(processed_funds)
    
    # 3. Load and prepare Market Indicators (KSE-100, Inflation, Interest rates)
    market_query = db.query(MarketIndicator).all()
    df_market = pd.DataFrame([{
        "date": pd.to_datetime(m.date),
        "kse100": m.kse100,
        "kibor_6m": m.kibor_6m,
        "inflation_rate": m.inflation_rate,
        "exchange_rate_usd": m.exchange_rate_usd
    } for m in market_query])
    
    if not df_market.empty:
        df_market = df_market.sort_values("date")
        # Calculate recent stock market return as an indicator
        df_market['kse100_return_30d'] = df_market['kse100'].pct_change(periods=30)
        # Merge market indicators into our main features table
        df_features = pd.merge(df_features, df_market, on="date", how="left")
        
    # 4. Load and calculate average news sentiment
    news_query = db.query(NewsArticle.published_at, NewsArticle.sentiment_score).all()
    df_news = pd.DataFrame([{
        "date": pd.to_datetime(n.published_at).date(), # Group by date
        "sentiment": n.sentiment_score
    } for n in news_query])
    
    if not df_news.empty:
        # Calculate average daily sentiment
        df_daily_sentiment = df_news.groupby("date")["sentiment"].mean().reset_index()
        df_daily_sentiment['date'] = pd.to_datetime(df_daily_sentiment['date'])
        
        # Since news sentiment on a single day is noisy, we compute a 7-day rolling average news sentiment
        df_daily_sentiment = df_daily_sentiment.sort_values("date")
        df_daily_sentiment['rolling_sentiment_7d'] = df_daily_sentiment['sentiment'].rolling(window=7, min_periods=1).mean()
        
        # Merge news sentiment into our main features table
        df_features = pd.merge(df_features, df_daily_sentiment[["date", "rolling_sentiment_7d"]], on="date", how="left")
    else:
        df_features['rolling_sentiment_7d'] = 0.0
        
    # 5. Clean up missing values
    # Fill missing market or sentiment values with defaults or forward fill
    df_features['rolling_sentiment_7d'] = df_features['rolling_sentiment_7d'].fillna(0.0)
    df_features = df_features.ffill().bfill()
    
    return df_features

if __name__ == "__main__":
    db = SessionLocal()
    try:
        df = get_engineered_features(db)
        if not df.empty:
            print(f"Engineered features shape: {df.shape}")
            print("\nSample features row:")
            print(df.iloc[-1][["date", "fund_name", "return_30d", "volatility_30d", "kse100_return_30d", "rolling_sentiment_7d", "target_return_30d"]])
    finally:
        db.close()
