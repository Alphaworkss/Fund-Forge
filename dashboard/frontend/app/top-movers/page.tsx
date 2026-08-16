"use client";

import React, { useEffect, useState } from "react";
import { ApiService } from "@/lib/api/services";
import { TopMoversResponse, MoverItem } from "@/lib/api/types";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { TrendingUp, TrendingDown, ArrowUpRight, Award, Flame } from "lucide-react";
import Link from "next/link";
import { formatCurrency, formatPercent, formatNumber } from "@/lib/formatters";

export default function TopMoversPage() {
  const [activeTab, setActiveTab] = useState<string>("all");
  const [horizon, setHorizon] = useState<string>("30d");
  const [data, setData] = useState<TopMoversResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMovers = () => {
    setLoading(true);
    setError(null);
    ApiService.getTopMovers(horizon, activeTab)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load top movers", err);
        setError(err?.message || "Failed to load top predicted movers.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchMovers();
  }, [horizon, activeTab]);

  const tabs = [
    { id: "all", label: "All Asset Classes" },
    { id: "crypto", label: "Cryptocurrencies" },
    { id: "stock", label: "Stocks" },
    { id: "mutual_fund", label: "Mutual Funds" },
    { id: "commodity", label: "Commodities" },
  ];

  const horizons = ["1d", "7d", "14d", "30d", "90d"];

  if (error) {
    return (
      <ErrorMessage
        title="Top Movers Data Unavailable"
        message={error}
        onRetry={fetchMovers}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero Header Banner */}
      <div className="bg-[#171f33] p-6 border border-[#2d3449] rounded-2xl shadow-xl">
        <div className="flex items-center gap-2.5 mb-1">
          <div className="p-2 rounded-xl bg-[#818cf8]/10 text-[#818cf8] border border-[#818cf8]/20">
            <Award className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-bold text-[#dae2fd]">
            SarmayaSaaz AI Top Predicted Movers
          </h1>
        </div>
        <p className="text-xs text-[#908f9e]">
          Highest gainers and top predicted decline candidates calculated across PatchTST, XGBoost and LightGBM model ensembles.
        </p>
      </div>

      {/* Asset Category Tabs + Horizon Picker aligned together */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#171f33] p-4 border border-[#2d3449] rounded-2xl shadow-lg">
        {/* Asset Category Tabs */}
        <div className="flex gap-2 overflow-x-auto max-w-full pb-1 sm:pb-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-[#818cf8] text-[#131e8c] shadow"
                  : "bg-[#0b1326] text-[#c6c5d5] hover:bg-[#222a3d] border border-[#2d3449]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Horizon Picker moved directly in front / alongside tabs */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[11px] font-mono text-[#908f9e] font-bold">Horizon:</span>
          <div className="flex items-center bg-[#0b1326] p-1 rounded-xl border border-[#2d3449]">
            {horizons.map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`px-2.5 py-1 text-xs font-mono font-bold rounded-lg transition-all uppercase ${
                  horizon === h
                    ? "bg-[#818cf8] text-[#131e8c] shadow"
                    : "text-[#c6c5d5] hover:text-[#dae2fd]"
                }`}
              >
                {h}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Hero Focus Grid: Top Gainers vs Top Losers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Gainers Column */}
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-[#171f33] p-4 rounded-2xl border border-[#4edea3]/40 shadow-xl">
            <div className="flex items-center gap-2 text-[#4edea3]">
              <Flame className="h-5 w-5 fill-[#4edea3]" />
              <h2 className="font-bold text-base text-[#dae2fd]">
                Top Gainers
              </h2>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30 uppercase">
              {horizon} Horizon
            </span>
          </div>

          {loading ? (
            <Skeleton className="h-96 w-full" />
          ) : (
            <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-4 shadow-xl space-y-3">
              {data?.gainers.map((item, idx) => (
                <MoverCard key={item.symbol} item={item} rank={idx + 1} isGainer={true} />
              ))}
            </div>
          )}
        </div>

        {/* Top Losers Column */}
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-[#171f33] p-4 rounded-2xl border border-[#ffb2b7]/40 shadow-xl">
            <div className="flex items-center gap-2 text-[#ffb2b7]">
              <TrendingDown className="h-5 w-5" />
              <h2 className="font-bold text-base text-[#dae2fd]">
                Top Losers
              </h2>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-[#ffb2b7]/10 text-[#ffb2b7] border border-[#ffb2b7]/30 uppercase">
              {horizon} Horizon
            </span>
          </div>

          {loading ? (
            <Skeleton className="h-96 w-full" />
          ) : (
            <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-4 shadow-xl space-y-3">
              {data?.losers.map((item, idx) => (
                <MoverCard key={item.symbol} item={item} rank={idx + 1} isGainer={false} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface MoverCardProps {
  item: MoverItem;
  rank: number;
  isGainer: boolean;
}

function MoverCard({ item, rank, isGainer }: MoverCardProps) {
  return (
    <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449] hover:border-[#818cf8]/40 transition-all flex items-center justify-between gap-3 font-mono">
      <div className="flex items-center gap-3 min-w-0">
        <span
          className={`w-6 h-6 shrink-0 rounded-lg flex items-center justify-center font-bold text-xs ${
            rank === 1
              ? "bg-[#818cf8] text-[#131e8c]"
              : "bg-[#171f33] text-[#908f9e] border border-[#2d3449]"
          }`}
        >
          {rank}
        </span>
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-1.5 truncate">
            <span className="font-bold text-xs text-[#dae2fd] truncate">{item.name}</span>
            <span className="text-xs text-[#818cf8] font-bold shrink-0">({item.symbol})</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-[#908f9e] font-sans truncate">
            <span className="uppercase px-1.5 py-0.2 rounded bg-[#171f33] border border-[#2d3449] shrink-0">
              {item.asset_type.replace("_", " ")}
            </span>
            <span className="truncate">• {item.model} ({formatNumber(item.confidence * 100)}%)</span>
          </div>
        </div>
      </div>

      {/* Price Target & Gain Badge - Fixed 2-Line Layout to prevent stretching */}
      <div className="flex items-center gap-3 text-right shrink-0">
        <div className="flex flex-col justify-center text-xs whitespace-nowrap leading-snug">
          <span className="text-[#908f9e] text-[11px]">
            Curr: {formatCurrency(item.current_price)}
          </span>
          <span className="font-bold text-[#dae2fd]">
            Target: {formatCurrency(item.predicted_target)}
          </span>
        </div>

        <span
          className={`flex items-center text-xs font-bold px-2.5 py-1 rounded-lg border whitespace-nowrap ${
            isGainer
              ? "bg-[#4edea3]/10 text-[#4edea3] border-[#4edea3]/30"
              : "bg-[#ffb2b7]/10 text-[#ffb2b7] border-[#ffb2b7]/30"
          }`}
        >
          {isGainer ? <TrendingUp className="h-3.5 w-3.5 mr-1" /> : <TrendingDown className="h-3.5 w-3.5 mr-1" />}
          {formatPercent(item.predicted_change_pct, 2, true)}
        </span>

        <Link
          href={`/?symbol=${item.symbol}`}
          className="p-1.5 rounded-lg bg-[#171f33] hover:bg-[#818cf8]/20 text-[#bdc2ff] border border-[#2d3449] hover:border-[#818cf8]/40 transition-colors"
          title="View Forecast & Chart"
        >
          <ArrowUpRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
