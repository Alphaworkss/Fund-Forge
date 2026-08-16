"use client";

import React, { useEffect, useState } from "react";
import { ApiService } from "@/lib/api/services";
import {
  BaseAsset,
  AllForecastsResponse,
  ModelInfoResponse,
  HistoryResponse,
  ForecastResponse,
  NewsResponse,
} from "@/lib/api/types";
import { AssetSelector } from "@/components/shared/AssetSelector";
import { PriceChart } from "@/components/charts/PriceChart";
import { ModelMetricsCard } from "@/components/forecast/ModelMetricsCard";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { Target } from "lucide-react";
import { formatCurrency, formatPercent } from "@/lib/formatters";

export default function ForecastsPage() {
  const [assets, setAssets] = useState<BaseAsset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<BaseAsset | null>(null);
  const [horizon, setHorizon] = useState<string>("30d");

  const [allForecasts, setAllForecasts] = useState<AllForecastsResponse | undefined>();
  const [forecast, setForecast] = useState<ForecastResponse | undefined>();
  const [history, setHistory] = useState<HistoryResponse | undefined>();
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | undefined>();
  const [news, setNews] = useState<NewsResponse | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAssets = () => {
    setLoading(true);
    setError(null);
    ApiService.getAssets()
      .then((res) => {
        setAssets(res.assets);
        if (res.assets.length > 0) setSelectedAsset(res.assets[0]);
      })
      .catch((err) => {
        console.error(err);
        setError(err?.message || "Failed to load assets.");
        setLoading(false);
      });
  };

  useEffect(() => {
    loadAssets();
  }, []);

  useEffect(() => {
    if (!selectedAsset) return;
    setLoading(true);
    setError(null);

    const sym = selectedAsset.symbol;
    Promise.all([
      ApiService.getAllForecasts(sym),
      ApiService.getForecast(sym, horizon),
      ApiService.getHistory(sym, horizon),
      ApiService.getModelInfo(sym),
      ApiService.getNews(sym),
    ])
      .then(([allFcRes, fcRes, histRes, modelRes, newsRes]) => {
        setAllForecasts(allFcRes);
        setForecast(fcRes);
        setHistory(histRes);
        setModelInfo(modelRes);
        setNews(newsRes);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err?.message || "Failed to load forecast data.");
        setLoading(false);
      });
  }, [selectedAsset, horizon]);

  if (error) {
    return (
      <ErrorMessage
        title="Forecast Data Unavailable"
        message={error}
        onRetry={() => {
          if (!selectedAsset) loadAssets();
          else setHorizon((prev) => prev);
        }}
      />
    );
  }

  if (!selectedAsset) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-[#dae2fd]">SarmayaSaaz AI Forecast Workspace</h1>
          <p className="text-xs text-[#908f9e]">
            Multi-horizon Target Ranges, Model Accuracy Metrics and Confidence Intervals.
          </p>
        </div>
        <AssetSelector
          assets={assets}
          selectedAsset={selectedAsset}
          onSelectAsset={(a) => setSelectedAsset(a)}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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

          {/* All Horizons Target Breakdown Table */}
          <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#2d3449]">
              <Target className="h-4 w-4 text-[#818cf8]" />
              <h3 className="font-semibold text-base text-[#dae2fd]">
                Multi-Horizon Target Price Matrix ({selectedAsset.symbol})
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse font-mono text-xs">
                <thead>
                  <tr className="border-b border-[#2d3449] text-[#908f9e] text-[10px]">
                    <th className="py-2.5 px-3">HORIZON</th>
                    <th className="py-2.5 px-3 text-right">LOWER BOUND</th>
                    <th className="py-2.5 px-3 text-right">EXPECTED TARGET</th>
                    <th className="py-2.5 px-3 text-right">UPPER BOUND</th>
                    <th className="py-2.5 px-3 text-center">DIRECTION</th>
                    <th className="py-2.5 px-3 text-right">CONFIDENCE</th>
                    <th className="py-2.5 px-3 text-right">MODEL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2d3449]">
                  {allForecasts?.forecasts.map((fc) => (
                    <tr
                      key={fc.horizon}
                      onClick={() => setHorizon(fc.horizon)}
                      className={`cursor-pointer transition-colors ${
                        horizon === fc.horizon
                          ? "bg-[#818cf8]/10 font-bold"
                          : "hover:bg-[#131b2e]/50"
                      }`}
                    >
                      <td className="py-3 px-3 uppercase text-[#818cf8]">
                        {fc.horizon}
                      </td>
                      <td className="py-3 px-3 text-right text-[#ffb2b7]">
                        {formatCurrency(fc.lower_bound)}
                      </td>
                      <td className="py-3 px-3 text-right text-[#dae2fd] font-bold">
                        {formatCurrency(fc.central_estimate)}
                      </td>
                      <td className="py-3 px-3 text-right text-[#4edea3]">
                        {formatCurrency(fc.upper_bound)}
                      </td>
                      <td className="py-3 px-3 text-center uppercase">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] ${
                            fc.direction === "bullish"
                              ? "bg-[#4edea3]/10 text-[#4edea3]"
                              : "bg-[#ffb2b7]/10 text-[#ffb2b7]"
                          }`}
                        >
                          {fc.direction}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right text-[#dae2fd]">
                        {formatPercent(fc.confidence * 100)}
                      </td>
                      <td className="py-3 px-3 text-right text-[#c6c5d5]">
                        {fc.model}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Model Leaderboard */}
        <div className="space-y-6">
          {loading ? (
            <Skeleton className="h-96 w-full" />
          ) : (
            <ModelMetricsCard modelInfo={modelInfo} />
          )}
        </div>
      </div>
    </div>
  );
}
