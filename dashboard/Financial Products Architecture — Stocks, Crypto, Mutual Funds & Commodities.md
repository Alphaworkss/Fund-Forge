# Financial Products Architecture
## Stocks, Cryptocurrencies, Mutual Funds & Commodities

This document extends the main `ARCHITECTURE.md`.

The platform must not be designed as a cryptocurrency-only application.

The system is a general **AI Financial Forecasting, Analysis, and Paper Trading Platform** supporting:

- Stocks
- Cryptocurrencies
- Mutual Funds
- Commodities

The architecture must be designed so additional financial products can be added later without restructuring the entire application.

---

# 1. Core Principle

The platform should treat every supported financial product as an **Asset**.

```text
Financial Product
       |
       +------------------+
       |                  |
     Asset              Asset Class
       |                  |
       |        +---------+---------+---------+
       |        |         |         |         |
       v        v         v         v         v
     AAPL     Stocks    Crypto   Mutual     Commodities
                                Funds
```

The frontend should not have completely separate applications for each asset class.

Instead:

```text
                    Financial Platform
                           |
                           v
                    Asset Abstraction
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
     Market             Forecast           Analysis
     Data                Data               Data
```

Asset-specific differences should be handled by the backend provider/service layer.

---

# 2. Supported Asset Classes

## 2.1 Stocks

Examples:

- Apple
- Microsoft
- NVIDIA
- Amazon
- Tesla
- Meta
- Alphabet

The system should eventually support a much larger universe of equities.

Stock-specific information can include:

- Current price
- Previous close
- Daily change
- Market capitalization
- Volume
- Sector
- Industry
- P/E ratio
- EPS
- Dividend yield
- 52-week high
- 52-week low
- Beta
- Earnings information
- Company news
- Technical indicators
- Forecast

---

# 2.2 Cryptocurrencies

Examples:

- Bitcoin
- Ethereum
- BNB
- Solana
- XRP
- Cardano
- Dogecoin
- Avalanche
- Chainlink

The existing crypto forecasting system should eventually be connected here.

Crypto-specific information can include:

- Current price
- 24-hour change
- Market capitalization
- Trading volume
- Circulating supply
- Total supply
- BTC dominance
- Exchange information
- On-chain metrics where available
- Crypto news
- Sentiment
- Technical indicators
- Forecast

The existing 136-coin forecasting pipeline should be treated as the future production forecasting provider for this asset class.

---

# 2.3 Mutual Funds

Mutual funds are fundamentally different from stocks and crypto and must not simply be treated as equities.

Potential information includes:

- NAV
- NAV change
- Fund category
- Fund manager
- Fund house
- Assets under management
- Expense ratio
- Management fee
- Risk level
- Historical returns
- Benchmark
- Asset allocation
- Equity allocation
- Debt allocation
- Cash allocation
- Geographic allocation
- Top holdings
- Fund performance
- Historical NAV
- Forecast/analysis where supported
- Fund news

The UI should use terminology appropriate to mutual funds.

For example:

```text
NAV
```

rather than:

```text
Stock Price
```

---

# 2.4 Commodities

The commodities system should support major commodities such as:

### Precious Metals

- Gold
- Silver
- Platinum
- Palladium

### Energy

- Crude Oil
- Brent Crude
- WTI Crude
- Natural Gas

### Agricultural

Potential future support:

- Wheat
- Corn
- Soybeans
- Coffee
- Sugar
- Cotton
- Cocoa

### Industrial / Other

Potential future support:

- Copper
- Aluminum
- Nickel

Commodity-specific information can include:

- Current price
- Unit
- Contract type
- Contract month where applicable
- Daily change
- Volume
- Open interest
- Historical prices
- Supply/demand information
- Inventory information
- Economic factors
- Commodity news
- Forecast

---

# 3. Asset Type System

Create a centralized asset-class enum.

Conceptually:

```python
class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    MUTUAL_FUND = "mutual_fund"
    COMMODITY = "commodity"
```

Do not scatter strings such as:

```text
"crypto"
"stock"
"stocks"
"mutual funds"
"commodity"
```

throughout the application.

Use one canonical representation.

---

# 4. Universal Asset Schema

All assets should share a base schema.

Conceptually:

```python
class Asset:
    symbol: str
    name: str
    asset_type: AssetType
    currency: str
    current_price: float
    change_24h: float
    last_updated: datetime
```

Then asset-specific schemas can extend this.

---

# 5. Asset-Specific Data

Universal fields:

```text
Symbol
Name
Asset Type
Current Value
Daily Change
Currency
Last Updated
```

Stock-specific:

```text
Market Cap
Sector
Industry
P/E
EPS
Dividend Yield
Volume
```

Crypto-specific:

```text
Market Cap
Volume
Circulating Supply
Total Supply
BTC Dominance
```

Mutual-fund-specific:

```text
NAV
AUM
Expense Ratio
Fund Manager
Fund Category
Benchmark
Risk Level
```

Commodity-specific:

```text
Unit
Contract
Contract Month
Volume
Open Interest
```

Do not force irrelevant fields onto every asset.

For example, a mutual fund does not need:

```text
P/E ratio
```

and a commodity does not need:

```text
Dividend Yield
```

---

# 6. Frontend Asset Selection

The main asset selector should support:

```text
Asset Class
   ↓
Asset
   ↓
Horizon
```

Example:

```text
Asset Class: Crypto
Asset: Bitcoin
Horizon: 30 Days
```

or:

```text
Asset Class: Stocks
Asset: NVIDIA
Horizon: 7 Days
```

or:

```text
Asset Class: Mutual Funds
Asset: XYZ Growth Fund
Horizon: 90 Days
```

or:

```text
Asset Class: Commodities
Asset: Gold
Horizon: 30 Days
```

The interface should dynamically adapt to the selected asset class.

---

# 7. Universal Forecast System

The forecasting interface should use a common structure.

Supported horizons:

```text
1D
7D
14D
30D
90D
```

However, the backend must be capable of enabling/disabling horizons by asset class.

For example:

```text
Crypto:
1D / 7D / 14D / 30D / 90D

Stocks:
1D / 7D / 14D / 30D / 90D

Mutual Funds:
7D / 14D / 30D / 90D

Commodities:
1D / 7D / 14D / 30D / 90D
```

The exact supported horizons should be configuration-driven.

Do not hard-code assumptions into the UI.

---

# 8. Forecast Output

The universal forecast response should support:

```text
Asset
Asset Type
Horizon
Current Value
Lower Bound
Upper Bound
Central Estimate
Expected Direction
Confidence
Model
Model Performance
Generated At
```

Example:

```json
{
  "symbol": "AAPL",
  "asset_type": "stock",
  "horizon": "30d",
  "current_value": 220.50,
  "lower_bound": 211.20,
  "upper_bound": 236.80,
  "central_estimate": 224.10,
  "direction": "bullish",
  "confidence": 0.76,
  "model": "XGBoost",
  "model_accuracy": 0.84
}
```

The same schema concept should work for:

- Stocks
- Crypto
- Mutual Funds
- Commodities

---

# 9. Forecast Provider Architecture

Each asset class may eventually use different forecasting models.

Use:

```text
ForecastService
       |
       v
ForecastProvider
       |
       +-------------------+
       |                   |
       v                   v
MockForecastProvider   Production Providers
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Stocks         Crypto       Commodities
             |
             v
       Mutual Funds
```

The exact implementation can use separate providers or a unified production forecasting service with asset-specific model registries.

---

# 10. Crypto Forecasting Provider

The crypto provider connects to the existing forecasting system.

Existing system characteristics:

- 136 cryptocurrencies
- Multi-horizon forecasting
- Walk-forward validation
- RobustScaler
- Multiple candidate models
- Best-model selection
- Model registry
- Feature importance
- SHAP
- Permutation importance
- Ablation analysis

Potential models:

- ARIMA
- Random Forest
- XGBoost
- LightGBM
- TFT
- PatchTST

The production provider should retrieve the selected winning model for each asset.

---

# 11. Stock Forecasting Provider

Stocks require their own forecasting pipeline.

Potential features:

### Price

- Open
- High
- Low
- Close
- Adjusted Close

### Volume

- Volume
- Volume change
- Volume moving averages

### Technical

- RSI
- MACD
- Moving averages
- Bollinger Bands
- ATR
- Momentum
- Volatility

### Fundamental

- P/E
- EPS
- Revenue
- Earnings growth
- Debt
- Free cash flow
- Dividend yield
- Market capitalization

### Market Context

- S&P 500
- Nasdaq
- Sector index
- VIX
- Interest rates

### News

- Company news
- Sector news
- Market news
- Sentiment

The stock forecasting provider should eventually use these features to generate forecast ranges.

---

# 12. Mutual Fund Forecasting Provider

Mutual funds require a specialized pipeline.

Potential inputs:

### NAV

- Historical NAV
- Daily/weekly NAV change
- Rolling returns
- Volatility

### Fund Characteristics

- Expense ratio
- AUM
- Fund category
- Fund manager
- Benchmark

### Holdings

- Top holdings
- Sector allocation
- Geographic allocation
- Equity/debt allocation

### Market Inputs

For equity funds:

- Relevant equity indices
- Major holdings
- Sector performance

For debt funds:

- Interest rates
- Bond yields
- Credit spreads

### News

- Fund-related news
- Market news
- Economic news

The system must recognize that mutual funds generally have different pricing frequency and liquidity characteristics from stocks/crypto.

Do not assume that every mutual fund has intraday prices.

---

# 13. Commodity Forecasting Provider

Commodities require specialized data.

Potential inputs:

### Price

- Spot price
- Futures price
- Historical prices
- Contract prices

### Futures Structure

Where applicable:

- Contract month
- Front-month contract
- Contango
- Backwardation
- Futures curve

### Market Data

- Volume
- Open interest
- Volatility

### Fundamental Drivers

Depending on commodity:

#### Gold

- Interest rates
- USD strength
- Inflation
- Central-bank demand
- Geopolitical risk

#### Oil

- OPEC production
- Inventory
- Global demand
- Production levels
- Geopolitical risk

#### Natural Gas

- Storage
- Weather
- Production
- LNG demand

#### Agricultural commodities

- Weather
- Crop conditions
- Production
- Exports
- Inventories

### Macro

- USD index
- Interest rates
- Inflation
- Global economic indicators

---

# 14. Important Commodity Data Constraint

The commodity data pipeline may initially have limited historical data availability.

Therefore the system MUST support:

```text
Mock Commodity Provider
```

even after the stock/crypto systems become operational.

Do not block the entire application because commodity historical data is unavailable.

When real commodity data becomes available, implement:

```text
MockCommodityProvider
        ↓
RealCommodityProvider
```

without changing the frontend API.

---

# 15. Mock Data Across All Asset Classes

The mock-data system must support all four categories.

Example:

```text
Stocks
AAPL
MSFT
NVDA
AMZN
TSLA

Crypto
BTC
ETH
SOL
XRP
BNB

Mutual Funds
Example Growth Fund
Example Balanced Fund
Example Income Fund

Commodities
Gold
Silver
WTI Crude
Brent Crude
Natural Gas
Copper
```

These are demonstration assets.

They must be clearly marked as simulated data.

---

# 16. Mock Data Consistency

Mock data must be internally consistent.

Example:

```text
AAPL
Current Price = $220
24h Change = +1.8%
```

The chart, forecast, market cards, and paper-trading system must use compatible values.

Likewise:

```text
Gold
Current Price = $X / oz
```

should use the correct commodity unit.

Mutual funds should display:

```text
NAV = X
```

rather than pretending NAV is a stock price.

---

# 17. Asset-Specific Units

The system must support units.

Examples:

```text
Stocks:
USD/share

Crypto:
USD/token

Mutual Funds:
USD/NAV

Gold:
USD/troy ounce

Silver:
USD/troy ounce

Crude Oil:
USD/barrel

Natural Gas:
USD/MMBtu
```

Do not hard-code `$` into every price component.

Use:

```text
value
currency
unit
```

as separate fields.

---

# 18. Historical Charts

The chart component should be reusable.

Conceptually:

```text
FinancialChart
       |
       +-- Stock
       +-- Crypto
       +-- Mutual Fund
       +-- Commodity
```

The chart should dynamically adapt:

### Stocks

Price over time.

### Crypto

Price over time.

### Mutual Funds

NAV over time.

### Commodities

Spot/futures price over time.

---

# 19. News and Factors

News should be asset-aware.

For stocks:

```text
Company News
Industry News
Market News
```

For crypto:

```text
Crypto News
Regulatory News
Market News
On-chain/Blockchain News
```

For mutual funds:

```text
Fund News
Underlying Market News
Economic News
```

For commodities:

```text
Commodity News
Supply/Demand News
Geopolitical News
Economic News
```

---

# 20. Explainability

The explainability interface should be universal.

The actual factors differ by asset class.

### Stocks

```text
Earnings
Momentum
Volume
Market Trend
Sector Performance
Valuation
News Sentiment
```

### Crypto

```text
Momentum
Volume
Volatility
BTC Trend
Market Sentiment
On-chain Metrics
News
```

### Mutual Funds

```text
Underlying Holdings
Sector Allocation
Market Trend
NAV Momentum
Interest Rates
Fund Flows
```

### Commodities

```text
Supply
Demand
Inventory
USD
Interest Rates
Weather
Geopolitical Risk
Futures Curve
```

---

# 21. Paper Trading Compatibility

Paper trading should be designed around an abstract tradable asset.

```text
PaperTrade
    |
    +-- Stock
    +-- Crypto
    +-- Commodity
```

Mutual funds should be handled according to their actual trading/subscription mechanics rather than pretending they behave exactly like exchange-traded assets.

The UI should adapt based on asset class.

---

# 22. Paper Trading Rules

For stocks:

- Buy
- Sell
- Position size
- P&L

For crypto:

- Buy
- Sell
- Position size
- P&L

For commodities:

- Simulated position
- Contract/unit handling
- P&L

For mutual funds:

- Buy/subscribe
- Redeem/sell
- NAV-based valuation
- P&L

Initially all of this can use mock market prices/NAVs.

---

# 23. Dashboard Adaptation

The dashboard should dynamically adapt to the selected asset class.

Example:

```text
Stock Dashboard
    |
    +-- Price
    +-- Market Cap
    +-- P/E
    +-- Earnings
    +-- Forecast
    +-- News
```

Crypto:

```text
Crypto Dashboard
    |
    +-- Price
    +-- Market Cap
    +-- Volume
    +-- Supply
    +-- Forecast
    +-- News
```

Mutual Fund:

```text
Mutual Fund Dashboard
    |
    +-- NAV
    +-- AUM
    +-- Expense Ratio
    +-- Allocation
    +-- Performance
    +-- Forecast/Analysis
```

Commodity:

```text
Commodity Dashboard
    |
    +-- Price
    +-- Unit
    +-- Contract
    +-- Supply/Demand
    +-- Forecast
    +-- News
```

The overall design language must remain consistent.

---

# 24. Common vs Asset-Specific Components

### Common components

```text
TopNavigation
AssetSelector
HorizonSelector
PriceCard
PerformanceCard
ForecastCard
ForecastChart
NewsCard
ModelCard
ConfidenceIndicator
FeatureImportance
LoadingState
ErrorState
```

### Asset-specific components

```text
StockFundamentals
CryptoMetrics
MutualFundMetrics
CommodityMetrics
CommodityContractInfo
FundAllocation
```

Avoid duplicating common components.

---

# 25. API Structure

Use asset-class-aware APIs.

Example:

```text
GET /api/assets
GET /api/assets/{symbol}
GET /api/assets/{symbol}/history
GET /api/assets/{symbol}/forecast
GET /api/assets/{symbol}/model
GET /api/assets/{symbol}/features
GET /api/assets/{symbol}/news
```

The response should include:

```text
asset_type
```

so the frontend knows how to render asset-specific information.

Optional filtered endpoint:

```text
GET /api/assets?type=stock
GET /api/assets?type=crypto
GET /api/assets?type=mutual_fund
GET /api/assets?type=commodity
```

---

# 26. Provider Architecture

Use separate providers where data requirements differ.

```text
AssetProvider
      |
      +-- StockProvider
      +-- CryptoProvider
      +-- MutualFundProvider
      +-- CommodityProvider
```

Forecasting:

```text
ForecastProvider
      |
      +-- StockForecastProvider
      +-- CryptoForecastProvider
      +-- MutualFundForecastProvider
      +-- CommodityForecastProvider
```

News:

```text
NewsProvider
      |
      +-- StockNewsProvider
      +-- CryptoNewsProvider
      +-- MutualFundNewsProvider
      +-- CommodityNewsProvider
```

---

# 27. Mock Provider Architecture

Every production provider must have a mock equivalent.

```text
MockStockProvider
MockCryptoProvider
MockMutualFundProvider
MockCommodityProvider
```

Likewise:

```text
MockStockForecastProvider
MockCryptoForecastProvider
MockMutualFundForecastProvider
MockCommodityForecastProvider
```

This guarantees that the entire UI can be developed before production data exists.

---

# 28. Configuration

Use:

```text
DATA_MODE=mock
```

Initially.

The system may later support:

```text
DATA_MODE=production
```

The provider factory decides which implementation to use.

Conceptually:

```python
if DATA_MODE == "mock":
    return MockProvider()

if DATA_MODE == "production":
    return ProductionProvider()
```

---

# 29. Database Design

Eventually PostgreSQL should contain generalized asset tables.

Conceptually:

```text
assets
------
id
symbol
name
asset_type
currency
unit
exchange
is_active
```

Then specialized tables:

```text
stock_metadata
crypto_metadata
mutual_fund_metadata
commodity_metadata
```

Historical data should not be stored in one enormous generic table if doing so creates poor query performance.

Use asset-appropriate historical-data structures.

---

# 30. Production Data Architecture

Eventually:

```text
                 Data Sources
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
    Stocks         Crypto         Commodities
       |              |              |
       +--------------+--------------+
                      |
                      v
                Data Pipeline
                      |
                      v
                  PostgreSQL
                      |
                      v
                Feature Pipeline
                      |
                      v
               Forecasting System
                      |
                      v
                  FastAPI
                      |
                      v
                 Next.js
```

Mutual fund data should enter through its own specialized data pipeline.

---

# 31. Forecasting Model Registry

The production system should support model selection independently for each asset.

Example:

```text
Asset       Best Model
--------------------------
BTC         PatchTST
ETH         LightGBM
AAPL        XGBoost
NVDA        TFT
Gold        LightGBM
Fund XYZ    XGBoost
```

The model registry must not assume that the same model is optimal for every asset class.

---

# 32. Model Evaluation

Each asset class should eventually have appropriate evaluation.

Common metrics:

```text
MAE
RMSE
MAPE
R²
```

Additional metrics can be introduced where appropriate.

Because the system predicts ranges, eventually consider range-specific metrics such as:

```text
Prediction Interval Coverage
Interval Width
Calibration
```

The initial dashboard may continue using the common metrics.

---

# 33. Asset-Class-Specific Feature Engineering

Do not create one universal feature-engineering pipeline.

Instead:

```text
FeaturePipeline
      |
      +-- StockFeatures
      +-- CryptoFeatures
      +-- MutualFundFeatures
      +-- CommodityFeatures
```

Shared preprocessing utilities can still be reused.

---

# 34. Data Frequency

The architecture must support different frequencies.

Examples:

```text
Crypto:
Hourly / Daily

Stocks:
Intraday / Daily

Mutual Funds:
Daily / Weekly depending on fund/data source

Commodities:
Intraday / Daily
```

Do not assume that every asset has hourly data.

The frontend should receive a normalized response with a frequency field.

---

# 35. Trading Calendar

The backend must eventually understand that different asset classes have different trading schedules.

Examples:

```text
Crypto:
24/7

Stocks:
Exchange trading hours

Mutual Funds:
Fund-specific NAV schedule

Commodities:
Exchange/contract-specific trading schedule
```

Do not assume that "market closed" has the same meaning for all asset classes.

---

# 36. Demo Mode

When running with:

```text
DATA_MODE=mock
```

the application should display a subtle:

```text
DEMO DATA
```

indicator.

All four asset classes must be fully navigable in demo mode.

A user should be able to demonstrate:

```text
Stocks
    ↓
AAPL
    ↓
Forecast
```

then:

```text
Crypto
    ↓
BTC
    ↓
Forecast
```

then:

```text
Mutual Funds
    ↓
Example Fund
    ↓
NAV / Forecast
```

then:

```text
Commodities
    ↓
Gold
    ↓
Forecast
```

without requiring any real data.

---

# 37. Future Expansion

The architecture should make it possible to add:

- ETFs
- Indices
- Bonds
- REITs
- Forex
- Other alternative assets

by adding:

```text
New AssetType
New Provider
New Schema
New Forecast Provider
New Asset-specific UI components
```

without rewriting the platform.

---

# 38. Important Implementation Rule

Do NOT create:

```text
crypto-dashboard/
stock-dashboard/
commodity-dashboard/
mutual-fund-dashboard/
```

as separate applications.

Create one:

```text
financial-platform/
```

with a generalized asset architecture.

---

# 39. Final Architecture

```text
                         FINANCIAL PLATFORM
                                |
                 +--------------+--------------+
                 |              |              |
              Stocks         Crypto        Mutual Funds
                 |              |              |
                 +--------------+--------------+
                                |
                           Commodities
                                |
                                v
                         Asset Abstraction
                                |
                +---------------+---------------+
                |               |               |
                v               v               v
             Market          Forecast       Analysis
              Data             Data            Data
                |               |               |
                +---------------+---------------+
                                |
                                v
                             FastAPI
                                |
                                v
                         Next.js Frontend
                                |
                                v
                              Vercel
```

---

# 40. Initial Development State

The first complete version should run entirely with mock data.

```text
Next.js
    |
    v
FastAPI
    |
    v
Mock Provider Layer
    |
    +-- Stocks
    +-- Crypto
    +-- Mutual Funds
    +-- Commodities
```

No real financial-data API should be required to demonstrate the application.

No real ML model should be required.

No PostgreSQL database should be required.

---

# 41. Production Migration

The final production architecture will become:

```text
                         USER
                           |
                           v
                     VERCEL / NEXT.JS
                           |
                           v
                       FASTAPI API
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
        PostgreSQL      ML Models      Data Services
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Stocks        Crypto      Commodities
             |
             v
        Mutual Funds
```

The frontend remains largely unchanged.

Only the provider/data/inference layers are replaced or connected to production systems.

---

# 42. Non-Negotiable Requirements

Antigravity must:

- Treat the platform as a multi-asset financial application.
- Support stocks.
- Support cryptocurrencies.
- Support mutual funds.
- Support commodities.
- Use a generalized asset abstraction.
- Use asset-specific providers where necessary.
- Use mock data for every asset class initially.
- Keep mock and production providers behind the same interfaces.
- Keep the existing crypto ML system intact.
- Do not force all asset classes into crypto-specific logic.
- Do not assume every asset has the same units.
- Do not assume every asset trades 24/7.
- Do not assume every asset has intraday pricing.
- Do not assume every asset has the same fundamental metrics.
- Make paper trading asset-aware.
- Make forecasts asset-aware.
- Make charts asset-aware.
- Make explainability asset-aware.
- Make news asset-aware.
- Keep the frontend independent of the ML implementation.
- Make the system ready for additional asset classes in the future.

---

# 43. Relationship With ARCHITECTURE.md

`ARCHITECTURE.md` defines the overall application architecture.

This document defines the **multi-asset financial-product architecture**.

If there is a conflict between the two documents, the implementation should preserve the following hierarchy:

```text
Application Architecture
        ↓
Multi-Asset Architecture
        ↓
Asset-Specific Architecture
        ↓
Implementation Details
```

The final application must be a **single unified financial platform**, not four separate applications.

The platform should be capable of beginning with realistic simulated data and progressively replacing individual data/forecast providers with production systems as they become available.