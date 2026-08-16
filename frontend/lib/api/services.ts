import { fetchApi } from './client';
import {
  AssetListResponse,
  BaseAsset,
  MarketOverviewResponse,
  HistoryResponse,
  ForecastResponse,
  AllForecastsResponse,
  ModelInfoResponse,
  FeatureImportanceResponse,
  NewsResponse,
  PortfolioState,
  TradeOrderRequest,
} from './types';

export const ApiService = {
  // Assets
  getAssets: (type?: string): Promise<AssetListResponse> =>
    fetchApi<AssetListResponse>(`/assets${type ? `?type=${type}` : ''}`),

  getAsset: (symbol: string): Promise<BaseAsset> =>
    fetchApi<BaseAsset>(`/assets/${symbol}`),

  // Market
  getMarketOverview: (type?: string): Promise<MarketOverviewResponse> =>
    fetchApi<MarketOverviewResponse>(`/market/overview${type ? `?type=${type}` : ''}`),

  // History
  getHistory: (symbol: string, period: string = '30d'): Promise<HistoryResponse> =>
    fetchApi<HistoryResponse>(`/history/${symbol}?period=${period}`),

  // Forecasts
  getForecast: (symbol: string, horizon: string = '30d'): Promise<ForecastResponse> =>
    fetchApi<ForecastResponse>(`/forecast/${symbol}?horizon=${horizon}`),

  getAllForecasts: (symbol: string): Promise<AllForecastsResponse> =>
    fetchApi<AllForecastsResponse>(`/forecast/${symbol}/all`),

  getTopMovers: (horizon: string = '30d', type?: string): Promise<import('./types').TopMoversResponse> =>
    fetchApi<import('./types').TopMoversResponse>(`/forecast/top-movers?horizon=${horizon}${type && type !== 'all' ? `&type=${type}` : ''}`),

  // Models
  getModelInfo: (symbol: string): Promise<ModelInfoResponse> =>
    fetchApi<ModelInfoResponse>(`/model/${symbol}`),

  // Features
  getFeatures: (symbol: string): Promise<FeatureImportanceResponse> =>
    fetchApi<FeatureImportanceResponse>(`/features/${symbol}`),

  // News
  getNews: (symbol: string): Promise<NewsResponse> =>
    fetchApi<NewsResponse>(`/news/${symbol}`),

  // Paper Trading
  getPortfolio: (): Promise<PortfolioState> =>
    fetchApi<PortfolioState>('/paper-trading/portfolio'),

  executeTrade: (trade: TradeOrderRequest): Promise<PortfolioState> =>
    fetchApi<PortfolioState>('/paper-trading/trade', {
      method: 'POST',
      body: JSON.stringify(trade),
    }),

  resetPortfolio: (): Promise<PortfolioState> =>
    fetchApi<PortfolioState>('/paper-trading/reset', {
      method: 'POST',
    }),
};
