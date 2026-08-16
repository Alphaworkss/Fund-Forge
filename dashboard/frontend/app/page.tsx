"use client";

import React, { useEffect, useState, Suspense } from "react";
import { ApiService } from "@/lib/api/services";
import {
  BaseAsset,
  ForecastResponse,
  HistoryResponse,
  FeatureImportanceResponse,
  ModelInfoResponse,
  NewsResponse,
} from "@/lib/api/types";
import { AssetSelector } from "@/components/shared/AssetSelector";
import { PriceChart } from "@/components/charts/PriceChart";
import { ForecastCard } from "@/components/forecast/ForecastCard";
import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";
import { StockFundamentalsCard } from "@/components/asset/StockFundamentalsCard";
import { CryptoMetricsCard } from "@/components/asset/CryptoMetricsCard";
import { MutualFundMetricsCard } from "@/components/asset/MutualFundMetricsCard";
import { CommodityMetricsCard } from "@/components/asset/CommodityMetricsCard";
import { DashboardNewsBox } from "@/components/dashboard/DashboardNewsBox";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { Cpu, TrendingUp, TrendingDown } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { formatCurrency, formatPercent } from "@/lib/formatters";
import { useHiddenFeatures } from "@/lib/featureFlags";

function DashboardContent() {
  const searchParams = useSearchParams();
  const symbolParam = searchParams.get("symbol");
  const hiddenFeaturesEnabled = useHiddenFeatures();

  const [assets, setAssets] = useState<BaseAsset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<BaseAsset | null>(null);
  const [horizon, setHorizon] = useState<string>("30d");

  const [history, setHistory] = useState<HistoryResponse | undefined>();
  const [forecast, setForecast] = useState<ForecastResponse | undefined>();
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | undefined>();
  const [features, setFeatures] = useState<FeatureImportanceResponse | undefined>();
  const [news, setNews] = useState<NewsResponse | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAssets = () => {
    setLoading(true);
    setError(null);
    ApiService.getAssets()
      .then((res) => {
        setAssets(res.assets);
        if (res.assets.length > 0) {
          const matched = symbolParam ? res.assets.find((a) => a.symbol.toUpperCase() === symbolParam.toUpperCase()) : null;
          setSelectedAsset(matched || res.assets[0]);
        } else {
          setError("No financial assets returned from backend.");
        }
      })
      .catch((err) => {
        console.error("Failed to load initial assets", err);
        setError(err?.message || "Failed to connect to the backend server.");
        setLoading(false);
      });
  };

  // Load initial asset catalog
  useEffect(() => {
    loadAssets();
  }, [symbolParam]);

  // Fetch detail data when selectedAsset or horizon changes
  useEffect(() => {
    if (!selectedAsset) return;
    setLoading(true);
    setError(null);

    const sym = selectedAsset.symbol;
    Promise.all([
      ApiService.getHistory(sym, horizon),
      ApiService.getForecast(sym, horizon),
      ApiService.getModelInfo(sym),
      ApiService.getFeatures(sym),
      ApiService.getNews(sym),
    ])
      .then(([histRes, fcRes, modelRes, featRes, newsRes]) => {
        setHistory(histRes);
        setForecast(fcRes);
        setModelInfo(modelRes);
        setFeatures(featRes);
        setNews(newsRes);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching asset details", err);
        setError(err?.message || "Failed to load asset metrics.");
        setLoading(false);
      });
  }, [selectedAsset, horizon]);

  if (error) {
    return (
      <ErrorMessage
        title="Dashboard Data Unavailable"
        message={error}
        onRetry={() => {
          if (!selectedAsset) loadAssets();
          else setHorizon((prev) => prev);
        }}
      />
    );
  }

  if (!selectedAsset) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  const isPositive = selectedAsset.change_24h_pct >= 0;

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl shadow-xl">
        <div className="flex flex-wrap items-center gap-4">
          <AssetSelector
            assets={assets}
            selectedAsset={selectedAsset}
            onSelectAsset={(a) => setSelectedAsset(a)}
          />

          <div className="flex flex-col font-mono">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-[#dae2fd]">
                {formatCurrency(selectedAsset.current_price)}
              </span>
              <span
                className={`flex items-center text-xs font-bold px-2 py-0.5 rounded-full ${
                  isPositive
                    ? "bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30"
                    : "bg-[#ffb2b7]/10 text-[#ffb2b7] border border-[#ffb2b7]/30"
                }`}
              >
                {isPositive ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                {formatPercent(selectedAsset.change_24h_pct, 2, true)}
              </span>
            </div>
            <span className="text-[11px] text-[#908f9e]">
              24h Change: {formatCurrency(selectedAsset.change_24h)} • Unit: {selectedAsset.unit}
            </span>
          </div>
        </div>

        {/* Quick Links */}
        <div className="flex items-center gap-3">
          <Link
            href="/forecasts"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#818cf8] hover:bg-[#818cf8]/90 text-[#131e8c] rounded-xl text-xs font-bold shadow transition-all"
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>Forecast Workspace</span>
          </Link>
        </div>
      </div>

      {/* Main Grid: Chart + Forecast & Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Price & Forecast Chart + Explainability */}
        <div className="lg:col-span-2 space-y-6">
          {loading ? (
            <Skeleton className="h-96 w-full" />
          ) : (
            <PriceChart
              history={history}
              forecast={forecast}
              news={news?.news}
              unit={selectedAsset.unit}
              selectedHorizon={horizon}
              onHorizonChange={(h) => setHorizon(h)}
            />
          )}

          {loading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <FeatureImportanceChart features={features} />
          )}
        </div>

        {/* Right Column (1 col): Forecast Target Card + Asset Metrics + Conditional News Box */}
        <div className="space-y-6">
          {loading ? (
            <Skeleton className="h-48 w-full" />
          ) : (
            <ForecastCard forecast={forecast} />
          )}

          {/* Dynamic Asset Metrics Card based on Asset Type */}
          {selectedAsset.asset_type === "stock" && (
            <StockFundamentalsCard asset={selectedAsset} />
          )}
          {selectedAsset.asset_type === "crypto" && (
            <CryptoMetricsCard asset={selectedAsset} />
          )}
          {selectedAsset.asset_type === "mutual_fund" && (
            <MutualFundMetricsCard asset={selectedAsset} />
          )}
          {selectedAsset.asset_type === "commodity" && (
            <CommodityMetricsCard asset={selectedAsset} />
          )}

          {/* Render Dashboard News Intelligence Box only when Hidden Features Activated */}
          {hiddenFeaturesEnabled && (
            <DashboardNewsBox news={news?.news} symbol={selectedAsset.symbol} />
          )}
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <DashboardContent />
    </Suspense>
  );
}
