# Crypto Forecasting Platform — Full Architecture Specification

## 1. Project Overview

This project is a web-based **AI Crypto Forecasting and Paper Trading Platform**.

The platform will provide users with:

- Cryptocurrency market information
- Historical price charts
- AI-generated price forecasts
- Forecast ranges for multiple time horizons
- Model information and model performance
- Factors influencing predictions
- Feature importance / explainability
- Relevant market/news information
- Paper trading / portfolio simulation
- Portfolio performance analytics
- A professional, production-quality dashboard UI

The frontend design is provided through **Google Stitch** and must be treated as the visual source of truth.

The application must initially work **without the real forecasting dataset or production ML models** by using a realistic mock-data system.

Later, the mock-data system will be replaced by the project's existing real Python forecasting/inference system.

---

# 2. Core Architectural Principle

The most important architectural requirement is:

> **The frontend must never depend directly on the ML models or raw datasets.**

The frontend communicates exclusively with the backend API.

The backend exposes stable API contracts.

The backend initially uses mock data.

Later, the backend can switch to the real forecasting/inference system without requiring the frontend to be rewritten.

### Current architecture

```text
Google Stitch Design
        |
        v
+---------------------------+
| Next.js Frontend          |
| React + TypeScript        |
| Tailwind CSS              |
+-------------+-------------+
              |
              | REST API
              v
+---------------------------+
| Python FastAPI Backend    |
+-------------+-------------+
              |
              v
+---------------------------+
| Mock Data Provider        |
+---------------------------+
```

### Future architecture

```text
+---------------------------+
| Next.js Frontend          |
| React + TypeScript        |
+-------------+-------------+
              |
              | HTTPS / REST API
              v
+---------------------------+
| Python FastAPI Backend    |
+-------------+-------------+
              |
      +-------+-------+
      |               |
      v               v
+-----------+   +-------------+
| ML        |   | PostgreSQL  |
| Inference |   | Database    |
+-----------+   +-------------+
      |
      v
Existing Crypto
Forecasting System
```

---

# 3. Technology Stack

## Frontend

Use:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide React
- Recharts or Apache ECharts

The frontend should use modern React patterns and reusable components.

---

## Backend

Use:

- Python
- FastAPI
- Pydantic
- Uvicorn

The backend is responsible for:

- API endpoints
- Data validation
- Forecast retrieval
- Model information
- Historical data retrieval
- Feature/explainability data
- News data
- Paper trading operations
- Mock-data access
- Future ML inference integration

---

## Database

The eventual production database should be:

- PostgreSQL

However, the initial frontend/backend must be able to run **without PostgreSQL**.

Mock data can initially be stored in:

```text
backend/app/data/mock/
```

using JSON files and/or Python-generated deterministic datasets.

---

## Deployment

### Frontend

Deploy using:

**Vercel**

### Backend

The FastAPI backend should be deployable independently using a Python-compatible hosting provider.

Possible future options include:

- Render
- Railway
- Fly.io
- AWS
- Google Cloud
- Azure

Do not tightly couple the backend to Vercel.

---

# 4. Repository Structure

Use a clean monorepo-style structure.

```text
crypto-forecasting-platform/
│
├── frontend/
│   ├── app/
│   │   ├── dashboard/
│   │   ├── paper-trading/
│   │   ├── forecasts/
│   │   ├── market/
│   │   ├── assets/
│   │   └── ...
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── navigation/
│   │   ├── charts/
│   │   ├── forecast/
│   │   ├── market/
│   │   ├── portfolio/
│   │   └── shared/
│   │
│   ├── lib/
│   │   ├── api/
│   │   ├── utils/
│   │   └── constants/
│   │
│   ├── types/
│   │
│   ├── public/
│   │
│   ├── .env.local
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── assets.py
│   │   │   │   ├── market.py
│   │   │   │   ├── forecasts.py
│   │   │   │   ├── history.py
│   │   │   │   ├── models.py
│   │   │   │   ├── features.py
│   │   │   │   ├── news.py
│   │   │   │   └── paper_trading.py
│   │   │   └── dependencies.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── assets.py
│   │   │   ├── forecasts.py
│   │   │   ├── market.py
│   │   │   ├── models.py
│   │   │   ├── features.py
│   │   │   └── paper_trading.py
│   │   │
│   │   ├── services/
│   │   │   ├── forecast_service.py
│   │   │   ├── market_service.py
│   │   │   ├── asset_service.py
│   │   │   ├── history_service.py
│   │   │   ├── model_service.py
│   │   │   ├── feature_service.py
│   │   │   ├── news_service.py
│   │   │   └── paper_trading_service.py
│   │   │
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   ├── mock/
│   │   │   │   ├── assets.py
│   │   │   │   ├── market.py
│   │   │   │   ├── forecasts.py
│   │   │   │   ├── history.py
│   │   │   │   ├── models.py
│   │   │   │   ├── features.py
│   │   │   │   ├── news.py
│   │   │   │   └── paper_trading.py
│   │   │   │
│   │   │   └── real/
│   │   │       └── README.md
│   │   │
│   │   ├── config/
│   │   │   └── settings.py
│   │   │
│   │   ├── data/
│   │   │   └── mock/
│   │   │       ├── assets.json
│   │   │       ├── forecasts.json
│   │   │       ├── market.json
│   │   │       ├── history.json
│   │   │       ├── models.json
│   │   │       ├── features.json
│   │   │       └── news.json
│   │   │
│   │   └── utils/
│   │
│   ├── requirements.txt
│   └── .env
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── API.md
│
├── .gitignore
└── README.md
```

---

# 5. Frontend Architecture

The frontend should be divided into:

```text
Pages
  |
  +-- Layout
  |
  +-- Reusable Components
  |
  +-- API Client
  |
  +-- State
  |
  +-- Types
```

Do not put API calls directly into every UI component.

Create a centralized API client.

Example conceptual structure:

```text
frontend/lib/api/
    client.ts
    assets.ts
    forecasts.ts
    market.ts
    history.ts
    models.ts
    features.ts
    news.ts
    paperTrading.ts
```

---

# 6. Common Navigation

All application pages must use a **common top navigation ribbon**.

The navigation must be consistent across all pages.

Do not create separate unrelated navigation bars for individual pages.

The navigation should provide access to the application's primary sections, based on the Google Stitch design.

Existing pages must be updated to use the common navigation without unnecessarily changing their other visual content.

---

# 7. Main Application Pages

The architecture should support the following major pages.

## Dashboard

The main overview page.

Possible sections include:

- Market overview
- Selected asset
- Current price
- 24-hour change
- Forecast summary
- Forecast range
- Historical/forecast chart
- Model information
- Confidence
- Key prediction factors
- Market statistics
- News
- Quick navigation

The exact visual layout must follow the Stitch design.

---

## Forecast Page

The forecasting interface should support:

### Assets

Initially support cryptocurrencies.

The architecture should allow future expansion to:

- Stocks
- Commodities
- Mutual Funds

### Horizons

Support:

- 1 day
- 7 days
- 14 days
- 30 days
- 90 days

### Forecast output

Return:

- Lower bound
- Upper bound
- Expected/central value where applicable
- Direction
- Confidence
- Model
- Model performance
- Prediction timestamp

---

## Paper Trading

The paper trading system must work completely with mock data.

It should support:

- Starting virtual capital
- Buy
- Sell
- Position size
- Holdings
- Cash balance
- Unrealized P&L
- Realized P&L
- Portfolio return
- Transaction history
- Portfolio value history
- Reset simulation

The paper trading system must not require a real exchange.

---

# 8. Mock Data System

The application MUST work even when:

- No real crypto data exists
- No trained model is available
- No PostgreSQL database exists
- No external API is available

The mock provider is therefore a first-class part of the architecture.

---

# 9. Mock Data Requirements

Mock data must be:

- Realistic
- Deterministic
- Internally consistent
- Stable between page refreshes unless intentionally randomized
- Sufficient to populate every dashboard component

Do NOT simply generate arbitrary random numbers independently for each component.

For example, if BTC's mock current price is:

```text
$118,420
```

then:

- The chart should be based around that value.
- The 24-hour change should correspond to a plausible previous price.
- Forecast ranges should be related to the current price.
- Paper trading prices should use the same mock market price.
- Asset cards should show the same values.

---

# 10. Mock Assets

Initially include a representative set of cryptocurrencies such as:

```text
BTC
ETH
BNB
SOL
XRP
ADA
DOGE
AVAX
LINK
DOT
MATIC
LTC
ATOM
UNI
NEAR
```

The architecture must support all 136 cryptocurrencies eventually.

Do not hard-code the UI around only these assets.

---

# 11. Historical Price Simulation

Generate realistic historical price series.

The generator should support:

```text
1D
7D
14D
30D
90D
1Y
```

The series should contain:

- Trend
- Volatility
- Minor fluctuations
- Larger market movements
- Occasional corrections
- Occasional spikes

Avoid obviously artificial straight lines.

The data should be deterministic using a fixed seed.

---

# 12. Forecast Simulation

Mock forecasts should simulate the output of the real ML system.

Each forecast should contain:

```json
{
  "symbol": "BTC",
  "horizon": "30d",
  "lower_bound": 108000,
  "upper_bound": 137500,
  "central_estimate": 123500,
  "direction": "bullish",
  "confidence": 0.78,
  "model": "PatchTST",
  "model_accuracy": 0.874,
  "generated_at": "..."
}
```

These numbers are demonstration values only.

The UI must clearly indicate when the application is running in demo/mock mode.

---

# 13. Forecast Horizons

The backend must support:

```text
1d
7d
14d
30d
90d
```

Do not implement separate frontend logic for every horizon.

Use a reusable horizon system.

Example:

```text
HORIZONS = [
    "1d",
    "7d",
    "14d",
    "30d",
    "90d"
]
```

---

# 14. Model Information

The system should be capable of displaying:

- Model name
- Model type
- Accuracy
- MAE
- RMSE
- R²
- MAPE
- Training period
- Last updated timestamp

Potential models include:

- ARIMA
- Random Forest
- XGBoost
- LightGBM
- TFT
- PatchTST

The final selected model for each cryptocurrency will eventually come from the existing model-selection system.

---

# 15. Existing ML System Integration

The existing forecasting system must remain separate from the UI.

Do not rewrite or duplicate the existing ML algorithms inside the frontend.

The backend should eventually provide an adapter layer.

Conceptually:

```text
ForecastService
      |
      v
ForecastProvider Interface
      |
      +----------------------+
      |                      |
      v                      v
MockForecastProvider   RealForecastProvider
                              |
                              v
                   Existing ML System
```

This is essential.

---

# 16. Provider Interface

Create provider abstractions.

Conceptually:

```python
class ForecastProvider:
    def get_forecast(self, symbol, horizon):
        raise NotImplementedError
```

Then:

```text
MockForecastProvider
RealForecastProvider
```

Both must return the same schema.

The frontend must not know which provider generated the data.

---

# 17. Environment Configuration

Use an environment variable:

```text
DATA_MODE=mock
```

Valid modes:

```text
mock
production
```

During initial development:

```text
DATA_MODE=mock
```

When the real ML pipeline is integrated:

```text
DATA_MODE=production
```

Do not require source-code modifications to switch between these modes.

---

# 18. API Design

Use REST APIs.

Base URL:

```text
/api
```

---

## Assets

```text
GET /api/assets
```

Returns supported assets.

---

## Market Overview

```text
GET /api/market/overview
```

Returns:

- Market status
- Total market capitalization
- Market change
- BTC dominance
- Top gainers
- Top losers
- Selected asset information

---

## Asset

```text
GET /api/assets/{symbol}
```

---

## Historical Data

```text
GET /api/history/{symbol}
```

Optional parameters:

```text
?period=30d
```

---

## Forecast

```text
GET /api/forecast/{symbol}
```

Optional:

```text
?horizon=30d
```

---

## All Forecasts

```text
GET /api/forecast/{symbol}/all
```

Returns:

```text
1d
7d
14d
30d
90d
```

---

## Model

```text
GET /api/model/{symbol}
```

---

## Features

```text
GET /api/features/{symbol}
```

Return feature importance / explanation information.

---

## News

```text
GET /api/news/{symbol}
```

Initially return mock news.

Later integrate the real news/data pipeline.

---

# 19. API Response Principles

All API responses must:

- Have predictable schemas
- Use Pydantic models
- Include useful error responses
- Validate inputs
- Avoid exposing internal filesystem paths
- Avoid exposing model files
- Avoid exposing secrets

Do not return arbitrary Python dictionaries where a defined schema is appropriate.

---

# 20. Error Handling

The frontend must handle:

- Loading
- Empty state
- API failure
- Invalid asset
- Invalid horizon
- Backend unavailable
- Missing forecast
- Missing model data

Never leave the interface blank because an API request failed.

Display a useful fallback state.

---

# 21. Loading States

Use proper loading states.

Examples:

- Skeleton cards
- Chart loading skeleton
- Forecast loading state
- Table loading state

Avoid unnecessary full-page loading screens.

---

# 22. Demo Mode Indicator

When:

```text
DATA_MODE=mock
```

the application should visibly indicate that the displayed market and forecast information is simulated/demo data.

Use wording such as:

```text
DEMO DATA
```

or:

```text
Simulation Mode
```

Do not make simulated predictions look like verified real financial predictions.

---

# 23. Paper Trading Data

Paper trading must use the same mock market provider as the rest of the application.

For example:

```text
Dashboard BTC price
        =
Paper Trading BTC price
        =
Mock Market BTC price
```

Do not create separate independent prices.

---

# 24. Paper Trading Architecture

Conceptually:

```text
Paper Trading UI
       |
       v
Paper Trading API
       |
       v
Paper Trading Service
       |
       +------> Market Provider
       |
       +------> Portfolio State
       |
       +------> Transaction History
```

The service should calculate:

- Average entry price
- Current market value
- Unrealized P&L
- Realized P&L
- Total return
- Cash balance
- Portfolio value

---

# 25. State Management

Use appropriate React state management.

Do not introduce a large state-management library unless necessary.

Local state should be used for:

- UI toggles
- Dropdowns
- Tabs
- Temporary selections

Shared application state can be used for:

- Selected asset
- Selected horizon
- Paper trading portfolio
- User preferences

---

# 26. Chart Requirements

Charts should be reusable components.

Examples:

```text
PriceChart
ForecastRangeChart
PortfolioChart
PerformanceChart
FeatureImportanceChart
```

The forecast chart should visually distinguish:

```text
Historical Price
Forecast Central Estimate
Lower Bound
Upper Bound
```

The exact visual style must follow the Stitch design.

---

# 27. Explainability

The dashboard should be able to display why a prediction was made.

Potential information:

- Feature importance
- SHAP values
- Permutation importance
- Market trend
- Volatility
- Momentum
- Volume
- BTC correlation
- Technical indicators
- News sentiment

Initially use mock explainability data.

Later connect it to the real explainability system.

---

# 28. News

The news section initially uses mock news objects.

Example:

```json
{
  "title": "Bitcoin market sentiment improves",
  "source": "Demo News",
  "timestamp": "...",
  "sentiment": "positive",
  "url": "#"
}
```

Do not use fabricated URLs that appear to be real sources.

Clearly mark demo content where necessary.

---

# 29. Security

Never expose:

- API keys
- Database credentials
- Model credentials
- Secret environment variables

The frontend must never receive server-side secrets.

Use environment variables.

Example:

```text
NEXT_PUBLIC_API_URL
```

for the public backend URL.

Server-only secrets must not use `NEXT_PUBLIC_`.

---

# 30. CORS

During local development, FastAPI should allow the local frontend origin:

```text
http://localhost:3000
```

Production CORS should be restricted to the deployed frontend domain.

Do not use unrestricted:

```text
allow_origins=["*"]
```

in production.

---

# 31. Local Development

The application must run locally with:

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

# 32. Environment Files

Frontend:

```text
frontend/.env.local
```

Example:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Backend:

```text
backend/.env
```

Example:

```text
DATA_MODE=mock
```

Do not commit real secrets.

---

# 33. Vercel Deployment

The frontend must be Vercel-compatible.

The frontend should obtain the backend URL from:

```text
NEXT_PUBLIC_API_URL
```

Local:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Production:

```text
NEXT_PUBLIC_API_URL=<production-fastapi-url>
```

Do not hard-code localhost into frontend API calls.

---

# 34. Backend Deployment

The backend should be stateless where practical.

It should be possible to deploy the FastAPI backend separately.

Do not assume that the backend runs on the same machine as Vercel.

---

# 35. Real ML Model Integration

When the actual models are available, the real provider should connect to the existing forecasting system.

The integration should support:

```text
Coin
    ↓
Feature Pipeline
    ↓
Preprocessing
    ↓
Selected Model
    ↓
Inference
    ↓
Forecast
    ↓
API Response
    ↓
Dashboard
```

The frontend should remain unchanged.

---

# 36. Model Selection Integration

The existing ML project evaluates multiple models per cryptocurrency.

Potential workflow:

```text
ARIMA
Random Forest
XGBoost
LightGBM
TFT
PatchTST
      |
      v
Evaluation
      |
      v
Best Model
      |
      v
Model Registry
      |
      v
RealForecastProvider
```

Only the selected/winning model should be used for production inference.

Archived models must not be unnecessarily loaded into memory.

---

# 37. Performance

The dashboard should:

- Avoid unnecessary API calls
- Cache stable data where appropriate
- Lazy-load heavy components
- Avoid loading all 136 cryptocurrency datasets into the browser
- Request only the selected asset's data when possible
- Keep chart datasets reasonably sized

Do not send raw large CSV datasets to the frontend.

The backend should aggregate/filter the data first.

---

# 38. Scalability

The architecture must eventually support:

```text
136+ cryptocurrencies
Multiple models
Multiple forecast horizons
Multiple users
Paper trading portfolios
Historical data
News
Explainability
```

Do not hard-code the application around BTC.

BTC should simply be the default selected asset.

---

# 39. Data Separation

Keep these concepts separate:

```text
Market Data
Forecast Data
Model Metadata
Feature Importance
News
Paper Trading State
```

Do not create one giant API response containing everything.

Use focused endpoints.

---

# 40. UI Implementation Rules

The Google Stitch design is the visual source of truth.

Antigravity must:

1. Inspect the provided Stitch design.
2. Reproduce the layout accurately.
3. Preserve the visual hierarchy.
4. Preserve spacing.
5. Preserve typography.
6. Preserve component placement.
7. Preserve colors.
8. Preserve responsive behavior.
9. Convert repeated visual elements into reusable components.
10. Make the components functional using the API.

Do not arbitrarily redesign the interface.

Do not add unnecessary UI elements simply because they are technically convenient.

---

# 41. Responsive Design

The dashboard must work on:

- Desktop
- Laptop
- Tablet
- Mobile

The desktop Stitch design is the primary reference.

Responsive behavior should be implemented without destroying the original visual hierarchy.

---

# 42. Accessibility

Use:

- Semantic HTML
- Keyboard navigation
- Accessible buttons
- Accessible labels
- Sufficient contrast
- Proper focus states
- ARIA only where necessary

---

# 43. Code Quality

Use:

- TypeScript strict mode
- Clear naming
- Small reusable components
- Separation of concerns
- Typed API responses
- Pydantic backend schemas
- Environment-based configuration

Avoid:

- Giant components
- Duplicate API logic
- Hard-coded mock values inside UI components
- Direct model imports inside React
- Direct database queries from the frontend
- Hard-coded localhost URLs
- Unnecessary dependencies

---

# 44. Mock-to-Production Migration

The migration should follow this pattern:

### Stage 1 — UI development

```text
Stitch
  ↓
Next.js
  ↓
FastAPI
  ↓
Mock Provider
```

### Stage 2 — Real data integration

```text
Stitch
  ↓
Next.js
  ↓
FastAPI
  ↓
Real Data Provider
```

### Stage 3 — Real ML integration

```text
Stitch
  ↓
Next.js
  ↓
FastAPI
  ↓
Real Forecast Provider
  ↓
Existing ML System
```

### Stage 4 — Production

```text
User
 ↓
Vercel
 ↓
Next.js
 ↓
Production FastAPI
 ↓
PostgreSQL + ML Models + Data Services
```

---

# 45. Development Priority

Implement in this order.

## Phase 1 — Foundation

- Repository structure
- Next.js setup
- TypeScript
- Tailwind
- shadcn/ui
- FastAPI
- Environment configuration
- CORS
- API client

## Phase 2 — Mock Data

- Asset provider
- Market provider
- Historical provider
- Forecast provider
- Model provider
- Feature provider
- News provider

## Phase 3 — Dashboard

- Common navigation
- Stitch layout
- Market cards
- Asset selection
- Price chart
- Forecast chart
- Forecast cards
- Model information
- Explainability
- News

## Phase 4 — Forecasting

- Forecast page
- Asset selection
- Horizon selection
- Forecast results
- Model information

## Phase 5 — Paper Trading

- Portfolio
- Buy
- Sell
- Positions
- Transactions
- P&L
- Performance chart
- Reset simulation

## Phase 6 — Polish

- Loading states
- Error states
- Responsive design
- Accessibility
- Animations where appropriate
- Performance optimization

## Phase 7 — Real Integration

- Connect real data
- Connect real model registry
- Connect real inference
- Connect explainability
- Connect news
- PostgreSQL integration

## Phase 8 — Deployment

- Deploy frontend to Vercel
- Deploy backend separately
- Configure environment variables
- Configure CORS
- Test production API connectivity

---

# 46. Important Constraints

Antigravity MUST follow these constraints.

### DO

- Use the Stitch design.
- Build reusable components.
- Use TypeScript.
- Use Next.js.
- Use FastAPI.
- Keep ML code in Python.
- Create a mock data provider.
- Make mock data realistic.
- Keep API contracts stable.
- Design for 136+ cryptocurrencies.
- Make paper trading functional with mock data.
- Make the transition to real data straightforward.
- Keep frontend and backend independently deployable.

### DO NOT

- Rewrite the existing ML system.
- Implement ML algorithms in JavaScript.
- Put model files inside the frontend.
- Put raw datasets inside the frontend.
- Hard-code data inside React components.
- Hard-code localhost URLs.
- Make the dashboard dependent on real data during initial development.
- Require PostgreSQL just to run the demo.
- Make fake predictions appear to be verified real predictions.
- Create unnecessary dependencies.
- Redesign the Stitch interface without a reason.

---

# 47. Definition of Done

The initial implementation is considered successful when:

- The frontend runs on localhost.
- The backend runs on localhost.
- The Stitch dashboard is implemented.
- The common navigation works.
- All dashboard components render.
- Mock market data is available.
- Historical charts work.
- Forecast ranges work.
- Multiple horizons work.
- Multiple cryptocurrencies work.
- Model information works.
- Feature/explainability information works.
- Mock news works.
- Paper trading works.
- Buy/sell operations work.
- Portfolio P&L works.
- Reset simulation works.
- Loading states work.
- Error states work.
- Responsive layout works.
- No real dataset is required.
- No trained model is required.
- The frontend communicates only through the backend API.
- `DATA_MODE=mock` successfully runs the complete application.
- The architecture leaves a clean path for `DATA_MODE=production`.
- The frontend is ready for Vercel deployment.

---

# 48. Final Implementation Principle

Build this as a **real production application with simulated data**, not as a disposable prototype.

The mock data is temporary.

The architecture is permanent.

The goal is that once the real crypto datasets, model registry, selected models, inference pipeline, news pipeline, and database become available, they can be connected behind the existing API without requiring a major frontend rewrite.

The most important separation is:

```text
                FRONTEND
                    |
                    | API
                    v
                BACKEND
                    |
            PROVIDER INTERFACE
              /           \
             /             \
        MOCK DATA       REAL DATA
                            |
                            v
                     EXISTING ML
                       SYSTEM
```

**The frontend should never know or care which provider is currently being used.**