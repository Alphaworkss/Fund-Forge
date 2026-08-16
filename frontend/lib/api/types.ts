export type AssetType = 'stock' | 'crypto' | 'mutual_fund' | 'commodity';

export interface BaseAsset {
  symbol: string;
  name: string;
  asset_type: AssetType;
  currency: string;
  unit: string;
  current_price: number;
  change_24h: number;
  change_24h_pct: number;
  sparkline_7d: number[];
  last_updated: string;
  metadata: Record<string, any>;
}

export interface AssetListResponse {
  assets: BaseAsset[];
  total: number;
  asset_types: string[];
}

export interface MarketOverviewStats {
  total_market_cap: number;
  market_cap_change_24h_pct: number;
  volume_24h: number;
  btc_dominance: number;
  fear_and_greed_index: number;
  fear_and_greed_label: string;
}

export interface MarketOverviewResponse {
  stats: MarketOverviewStats;
  top_gainers: BaseAsset[];
  top_losers: BaseAsset[];
  trending_assets: BaseAsset[];
  featured_asset: BaseAsset;
}

export interface PricePoint {
  timestamp: string;
  price: number;
  volume: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface HistoryResponse {
  symbol: string;
  asset_type: string;
  period: string;
  unit: string;
  points: PricePoint[];
}

export interface ForecastPoint {
  timestamp: string;
  central_estimate: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResponse {
  symbol: string;
  asset_type: string;
  horizon: string;
  current_value: number;
  lower_bound: number;
  upper_bound: number;
  central_estimate: number;
  direction: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  model: string;
  model_accuracy: number;
  mae: number;
  rmse: number;
  generated_at: string;
  forecast_series: ForecastPoint[];
}

export interface AllForecastsResponse {
  symbol: string;
  asset_type: string;
  forecasts: ForecastResponse[];
}

export interface ModelMetric {
  name: string;
  architecture: string;
  r2_score: number;
  mae: number;
  rmse: number;
  mape_pct: number;
  is_winning_model: boolean;
  training_period: string;
}

export interface ModelInfoResponse {
  symbol: string;
  asset_type: string;
  selected_model: string;
  winning_metric: ModelMetric;
  candidate_models: ModelMetric[];
  last_trained: string;
}

export interface FeatureFactor {
  name: string;
  category: string;
  shap_value: number;
  impact: string;
  description: string;
}

export interface FeatureImportanceResponse {
  symbol: string;
  asset_type: string;
  factors: FeatureFactor[];
  summary: string;
}

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  timestamp: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  asset_symbol: string;
  asset_type: string;
  url: string;
}

export interface NewsResponse {
  symbol: string;
  news: NewsItem[];
}

export interface PositionHolding {
  symbol: string;
  name: string;
  asset_type: string;
  quantity: number;
  avg_buy_price: number;
  current_price: number;
  current_market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface TradeTransaction {
  id: string;
  timestamp: string;
  symbol: string;
  asset_type: string;
  action: string;
  quantity: number;
  execution_price: number;
  total_cost: number;
}

export interface PortfolioState {
  starting_balance: number;
  cash_balance: number;
  holdings_value: number;
  total_portfolio_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  realized_pnl: number;
  realized_pnl_pct: number;
  total_return_pct: number;
  holdings: PositionHolding[];
  recent_transactions: TradeTransaction[];
  asset_allocation: Record<string, number>;
}

export interface TradeOrderRequest {
  symbol: string;
  action: 'buy' | 'sell';
  quantity: number;
}

export interface MoverItem {
  symbol: string;
  name: string;
  asset_type: string;
  current_price: number;
  predicted_target: number;
  predicted_change_pct: number;
  direction: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  model: string;
  unit: string;
}

export interface TopMoversResponse {
  horizon: string;
  asset_type?: string;
  gainers: MoverItem[];
  losers: MoverItem[];
}

