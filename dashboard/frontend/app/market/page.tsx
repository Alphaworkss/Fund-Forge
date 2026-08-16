"use client";

import React, { useEffect, useState } from "react";
import { ApiService } from "@/lib/api/services";
import { BaseAsset } from "@/lib/api/types";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { Search, Flame, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { formatCurrency, formatPercent } from "@/lib/formatters";

export default function MarketPage() {
  const [assets, setAssets] = useState<BaseAsset[]>([]);
  const [activeTab, setActiveTab] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssets = () => {
    setLoading(true);
    setError(null);
    ApiService.getAssets()
      .then((res) => {
        setAssets(res.assets);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err?.message || "Failed to connect to backend market service.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const tabs = [
    { id: "all", label: "All Asset Classes" },
    { id: "crypto", label: "Cryptocurrencies" },
    { id: "stock", label: "Stocks" },
    { id: "mutual_fund", label: "Mutual Funds" },
    { id: "commodity", label: "Commodities" },
  ];

  const filteredAssets = assets.filter((asset) => {
    const matchesTab = activeTab === "all" || asset.asset_type === activeTab;
    const matchesSearch =
      asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.symbol.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTab && matchesSearch;
  });

  if (error) {
    return (
      <ErrorMessage
        title="Market Explorer Unavailable"
        message={error}
        onRetry={fetchAssets}
      />
    );
  }

  if (loading) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-[#dae2fd]">SarmayaSaaz Global Market Explorer</h1>
          <p className="text-xs text-[#908f9e]">
            Real-time quotes, technical metrics and multi-asset intelligence.
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-72">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search symbol, company, commodity..."
            className="w-full bg-[#0b1326] text-[#dae2fd] placeholder-[#908f9e] text-xs rounded-xl pl-9 pr-3 py-2 border border-[#2d3449] focus:outline-none focus:border-[#818cf8] transition-colors"
          />
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#908f9e]" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 border-b border-[#2d3449]">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
              activeTab === tab.id
                ? "bg-[#818cf8] text-[#131e8c] shadow"
                : "bg-[#171f33] text-[#c6c5d5] hover:bg-[#222a3d]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Market Catalog Table */}
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b border-[#2d3449] text-[#908f9e] text-[10px]">
                <th className="py-3 px-3">ASSET & TICKER</th>
                <th className="py-3 px-3">CATEGORY</th>
                <th className="py-3 px-3 text-right">CURRENT PRICE</th>
                <th className="py-3 px-3 text-right">24H CHANGE</th>
                <th className="py-3 px-3 text-right">UNIT</th>
                <th className="py-3 px-3 text-center">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3449]">
              {filteredAssets.map((asset) => {
                const isPositive = asset.change_24h_pct >= 0;
                // Peaked interest criteria: high 24h volatility (> 2.5%) or market leaders
                const isPeakedInterest = Math.abs(asset.change_24h_pct) >= 2.50 || asset.symbol === "BTC" || asset.symbol === "NVDA";

                return (
                  <tr key={asset.symbol} className="hover:bg-[#131b2e]/50 transition-colors">
                    <td className="py-3 px-3">
                      <div className="flex flex-col">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-[#dae2fd] text-sm font-sans">{asset.name}</span>
                          {/* Flame symbol placed AFTER asset name for page symmetry */}
                          {isPeakedInterest && (
                            <span title="Peaked Market Interest (High Volume Spike / Trending)">
                              <Flame className="h-4 w-4 text-amber-500 fill-amber-500 animate-pulse shrink-0" />
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-[#818cf8]">{asset.symbol}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 uppercase text-[10px]">
                      <span className="px-2 py-0.5 rounded bg-[#0b1326] text-[#c6c5d5] border border-[#2d3449]">
                        {asset.asset_type.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-bold text-[#dae2fd] text-sm">
                      {formatCurrency(asset.current_price)}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span
                        className={`inline-flex items-center font-bold ${
                          isPositive ? "text-[#4edea3]" : "text-[#ffb2b7]"
                        }`}
                      >
                        {formatPercent(asset.change_24h_pct, 2, true)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right text-[#908f9e] text-[11px]">
                      {asset.unit}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <Link
                        href={`/?symbol=${asset.symbol}`}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-[#818cf8]/10 hover:bg-[#818cf8]/20 border border-[#818cf8]/30 text-[#818cf8] text-[11px] rounded-lg font-bold transition-all"
                      >
                        <span>Forecast</span>
                        <ArrowUpRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
