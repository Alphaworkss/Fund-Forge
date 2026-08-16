"use client";

import React, { useEffect, useState } from "react";
import { ApiService } from "@/lib/api/services";
import { BaseAsset, PortfolioState, PositionHolding } from "@/lib/api/types";
import { TradeModal } from "@/components/portfolio/TradeModal";
import { HoldingsTable } from "@/components/portfolio/HoldingsTable";
import { TransactionHistory } from "@/components/portfolio/TransactionHistory";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  PlusCircle,
  RotateCcw,
  PieChart,
  DollarSign,
  Briefcase,
} from "lucide-react";

export default function PaperTradingPage() {
  const [portfolio, setPortfolio] = useState<PortfolioState | undefined>();
  const [assets, setAssets] = useState<BaseAsset[]>([]);
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);
  const [tradeModalAsset, setTradeModalAsset] = useState<BaseAsset | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolio = () => {
    setLoading(true);
    setError(null);
    Promise.all([ApiService.getPortfolio(), ApiService.getAssets()])
      .then(([portRes, assetRes]) => {
        setPortfolio(portRes);
        setAssets(assetRes.assets);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err?.message || "Failed to load paper trading portfolio.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const handleReset = async () => {
    if (window.confirm("Are you sure you want to reset your paper trading simulation to initial $100,000 balance?")) {
      await ApiService.resetPortfolio();
      fetchPortfolio();
    }
  };

  const handleSellHolding = (holding: PositionHolding) => {
    const matchedAsset = assets.find((a) => a.symbol === holding.symbol);
    setTradeModalAsset(matchedAsset);
    setIsTradeModalOpen(true);
  };

  if (error) {
    return (
      <ErrorMessage
        title="Paper Trading Simulator Unavailable"
        message={error}
        onRetry={fetchPortfolio}
      />
    );
  }

  if (loading || !portfolio) return <Skeleton className="h-96 w-full" />;

  const isReturnPositive = portfolio.total_return_pct >= 0;

  return (
    <div className="space-y-6">
      {/* Top Banner & Control Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-[#dae2fd]">
            Paper Trading & Portfolio Simulator
          </h1>
          <p className="text-xs text-[#908f9e]">
            Risk-free virtual capital investment simulation across Stocks, Crypto, Mutual Funds, and Commodities.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setTradeModalAsset(undefined);
              setIsTradeModalOpen(true);
            }}
            className="flex items-center gap-1.5 px-4 py-2 bg-[#818cf8] hover:bg-[#818cf8]/90 text-[#131e8c] rounded-xl text-xs font-bold shadow transition-all active:scale-95"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Execute Trade Order</span>
          </button>
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#0b1326] hover:bg-[#ffb2b7]/20 border border-[#2d3449] hover:border-[#ffb2b7]/40 text-[#c6c5d5] hover:text-[#ffb2b7] rounded-xl text-xs font-semibold transition-all"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset Simulation</span>
          </button>
        </div>
      </div>

      {/* Portfolio Analytics Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        <div className="bg-[#171f33] p-4 rounded-2xl border border-[#2d3449] shadow-md">
          <div className="flex items-center gap-2 text-[#908f9e] text-[11px] mb-1">
            <Wallet className="h-3.5 w-3.5 text-[#818cf8]" />
            <span>TOTAL PORTFOLIO VALUE</span>
          </div>
          <span className="text-xl font-bold text-[#dae2fd]">
            ${portfolio.total_portfolio_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
          <div className="text-[10px] text-[#908f9e] mt-1">
            Cash: ${portfolio.cash_balance.toLocaleString()}
          </div>
        </div>

        <div className="bg-[#171f33] p-4 rounded-2xl border border-[#2d3449] shadow-md">
          <div className="flex items-center gap-2 text-[#908f9e] text-[11px] mb-1">
            <Briefcase className="h-3.5 w-3.5 text-[#4edea3]" />
            <span>HOLDINGS VALUE</span>
          </div>
          <span className="text-xl font-bold text-[#dae2fd]">
            ${portfolio.holdings_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
          <div className="text-[10px] text-[#908f9e] mt-1">
            {portfolio.holdings.length} Active Asset Positions
          </div>
        </div>

        <div className="bg-[#171f33] p-4 rounded-2xl border border-[#2d3449] shadow-md">
          <div className="flex items-center gap-2 text-[#908f9e] text-[11px] mb-1">
            <TrendingUp className="h-3.5 w-3.5 text-[#818cf8]" />
            <span>UNREALIZED P&L</span>
          </div>
          <span
            className={`text-xl font-bold ${
              portfolio.unrealized_pnl >= 0 ? "text-[#4edea3]" : "text-[#ffb2b7]"
            }`}
          >
            {portfolio.unrealized_pnl >= 0 ? "+" : ""}$
            {portfolio.unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
          <div className="text-[10px] text-[#908f9e] mt-1">
            ({portfolio.unrealized_pnl >= 0 ? "+" : ""}{portfolio.unrealized_pnl_pct}%)
          </div>
        </div>

        <div className="bg-[#171f33] p-4 rounded-2xl border border-[#2d3449] shadow-md">
          <div className="flex items-center gap-2 text-[#908f9e] text-[11px] mb-1">
            <DollarSign className="h-3.5 w-3.5 text-[#818cf8]" />
            <span>TOTAL SIMULATION RETURN</span>
          </div>
          <span
            className={`text-xl font-bold ${
              isReturnPositive ? "text-[#4edea3]" : "text-[#ffb2b7]"
            }`}
          >
            {isReturnPositive ? "+" : ""}{portfolio.total_return_pct}%
          </span>
          <div className="text-[10px] text-[#908f9e] mt-1">
            Realized P&L: ${portfolio.realized_pnl.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Asset Allocation Breakdown */}
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[#2d3449]">
          <PieChart className="h-4 w-4 text-[#818cf8]" />
          <h3 className="font-semibold text-sm text-[#dae2fd]">
            Multi-Asset Portfolio Allocation Breakdown
          </h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          {Object.entries(portfolio.asset_allocation).map(([type, pct]) => (
            <div key={type} className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
              <span className="text-[#908f9e] text-[10px] uppercase block">
                {type.replace("_", " ")}
              </span>
              <span className="text-[#dae2fd] font-bold text-sm">{pct}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Holdings Table */}
      <HoldingsTable
        holdings={portfolio.holdings}
        onSellClick={(h) => handleSellHolding(h)}
      />

      {/* Transaction History Log */}
      <TransactionHistory transactions={portfolio.recent_transactions} />

      {/* Trade Execution Modal */}
      <TradeModal
        assets={assets}
        initialAsset={tradeModalAsset}
        isOpen={isTradeModalOpen}
        onClose={() => setIsTradeModalOpen(false)}
        onSuccess={() => fetchPortfolio()}
      />
    </div>
  );
}
