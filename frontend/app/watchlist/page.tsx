"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Bookmark,
  TrendingUp,
  Zap,
  Target,
  AlertTriangle,
  Plus,
  CheckCircle2,
  MoreVertical,
  Search,
  X,
  Bell,
  BellOff,
  Trash2,
  ExternalLink,
  AlertCircle,
} from "lucide-react";
import { ApiService } from "@/lib/api/services";
import { BaseAsset } from "@/lib/api/types";
import { formatPercent, formatCurrency } from "@/lib/formatters";

interface TrackedAsset {
  symbol: string;
  name: string;
  category: string;
  price: number;
  change1d: number;
  forecast30d: number;
  potential: number;
  accuracy: number;
  risk: "Low" | "Medium" | "High";
  iconText: string;
  iconBg: string;
  activeAlert?: {
    targetPrice: number;
    condition: "Above" | "Below";
  };
}

export default function WatchlistPage() {
  const router = useRouter();

  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [addSearchQuery, setAddSearchQuery] = useState<string>("");
  const [activeRowAction, setActiveRowAction] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const [errorModalMessage, setErrorModalMessage] = useState<string | null>(null);

  // Price Alert Modal State
  const [alertingAsset, setAlertingAsset] = useState<TrackedAsset | null>(null);
  const [alertPriceInput, setAlertPriceInput] = useState<string>("");
  const [alertCondition, setAlertCondition] = useState<"Above" | "Below">("Above");

  // Full Backend Asset Catalog
  const [fullCatalog, setFullCatalog] = useState<BaseAsset[]>([]);

  const defaultWatchlist: TrackedAsset[] = [
    {
      symbol: "NVDA",
      name: "NVIDIA Corp",
      category: "Technology • Semiconductors",
      price: 974.20,
      change1d: 2.40,
      forecast30d: 1150.20,
      potential: 18.07,
      accuracy: 88.00,
      risk: "Medium",
      iconText: "N",
      iconBg: "bg-[#818cf8]/20 text-[#818cf8]",
    },
    {
      symbol: "BTC",
      name: "Bitcoin",
      category: "Cryptocurrency • Layer 1",
      price: 64230.50,
      change1d: -1.20,
      forecast30d: 72000.00,
      potential: 12.10,
      accuracy: 76.00,
      risk: "High",
      iconText: "₿",
      iconBg: "bg-amber-500/20 text-amber-400",
      activeAlert: {
        targetPrice: 70000.00,
        condition: "Above",
      },
    },
    {
      symbol: "XAU/USD",
      name: "Gold",
      category: "Commodities • Precious Metals",
      price: 2340.10,
      change1d: 0.50,
      forecast30d: 2410.00,
      potential: 2.99,
      accuracy: 94.20,
      risk: "Low",
      iconText: "Au",
      iconBg: "bg-yellow-500/20 text-yellow-400",
    },
    {
      symbol: "AAPL",
      name: "Apple Inc.",
      category: "Technology • Consumer Electronics",
      price: 224.30,
      change1d: 1.15,
      forecast30d: 245.00,
      potential: 9.23,
      accuracy: 91.50,
      risk: "Low",
      iconText: "A",
      iconBg: "bg-blue-500/20 text-blue-400",
    },
    {
      symbol: "ETH",
      name: "Ethereum",
      category: "Cryptocurrency • Smart Contracts",
      price: 3450.00,
      change1d: 3.20,
      forecast30d: 3950.00,
      potential: 14.49,
      accuracy: 82.30,
      risk: "Medium",
      iconText: "Ξ",
      iconBg: "bg-indigo-500/20 text-indigo-400",
    },
    {
      symbol: "GROWTH_FUND",
      name: "SarmayaSaaz Global Tech Growth Fund",
      category: "Mutual Funds • Equity Growth",
      price: 145.20,
      change1d: 0.85,
      forecast30d: 158.00,
      potential: 8.82,
      accuracy: 89.00,
      risk: "Low",
      iconText: "SF",
      iconBg: "bg-emerald-500/20 text-emerald-400",
    },
  ];

  const [watchlist, setWatchlist] = useState<TrackedAsset[]>([]);
  const [isLoaded, setIsLoaded] = useState<boolean>(false);

  // Load backend asset catalog
  useEffect(() => {
    ApiService.getAssets()
      .then((res) => setFullCatalog(res.assets))
      .catch((err) => console.error("Failed to load backend asset catalog", err));
  }, []);

  // Load watchlist from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("sarmayasaaz_watchlist");
      if (saved) {
        setWatchlist(JSON.parse(saved));
      } else {
        setWatchlist(defaultWatchlist);
      }
    } catch (e) {
      setWatchlist(defaultWatchlist);
    }
    setIsLoaded(true);
  }, []);

  // Save watchlist to localStorage on change
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem("sarmayasaaz_watchlist", JSON.stringify(watchlist));
    }
  }, [watchlist, isLoaded]);

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3500);
  };

  const handleAddAsset = (asset: TrackedAsset) => {
    // Check if asset already exists in watchlist
    if (watchlist.some((item) => item.symbol.toUpperCase() === asset.symbol.toUpperCase())) {
      setErrorModalMessage(`Asset "${asset.name} (${asset.symbol})" is already in your active watchlist.`);
      return;
    }
    setWatchlist([asset, ...watchlist]);
    showToast(`Added ${asset.symbol} to Watchlist!`);
    setIsAddModalOpen(false);
  };

  const handleRemoveAsset = (symbol: string) => {
    setWatchlist(watchlist.filter((item) => item.symbol !== symbol));
    setActiveRowAction(null);
    showToast(`Removed ${symbol} from Watchlist.`);
  };

  const handleOpenPriceAlertModal = (asset: TrackedAsset) => {
    setActiveRowAction(null);
    setAlertingAsset(asset);
    setAlertCondition("Above");
    setAlertPriceInput((asset.price * 1.05).toFixed(2));
  };

  const handleSelectAlertCondition = (cond: "Above" | "Below") => {
    setAlertCondition(cond);
    if (alertingAsset) {
      if (cond === "Above") {
        setAlertPriceInput((alertingAsset.price * 1.05).toFixed(2));
      } else {
        setAlertPriceInput((alertingAsset.price * 0.95).toFixed(2));
      }
    }
  };

  const handleRemovePriceAlert = (symbol: string) => {
    const updated = watchlist.map((item) => {
      if (item.symbol === symbol) {
        const { activeAlert, ...rest } = item;
        return rest;
      }
      return item;
    });
    setWatchlist(updated);
    setActiveRowAction(null);
    showToast(`Price alert removed for ${symbol}.`);
  };

  const handleSavePriceAlert = () => {
    if (!alertingAsset) return;
    const numPrice = parseFloat(alertPriceInput);
    if (isNaN(numPrice) || numPrice <= 0) {
      showToast("Please enter a valid price threshold.");
      return;
    }

    // Strict validation: "Rises Above" requires target price > current price
    if (alertCondition === "Above" && numPrice <= alertingAsset.price) {
      showToast(`Target alert price must be higher than current price (${formatCurrency(alertingAsset.price)}) for "Rises Above" alert.`);
      return;
    }

    // Strict validation: "Drops Below" requires target price < current price
    if (alertCondition === "Below" && numPrice >= alertingAsset.price) {
      showToast(`Target alert price must be lower than current price (${formatCurrency(alertingAsset.price)}) for "Drops Below" alert.`);
      return;
    }

    const updated = watchlist.map((item) => {
      if (item.symbol === alertingAsset.symbol) {
        return {
          ...item,
          activeAlert: {
            targetPrice: numPrice,
            condition: alertCondition,
          },
        };
      }
      return item;
    });

    setWatchlist(updated);
    showToast(`Price Alert set for ${alertingAsset.symbol}: Triggers when price goes ${alertCondition} ${formatCurrency(numPrice)}`);
    setAlertingAsset(null);
  };

  // Convert BaseAsset from backend API into TrackedAsset format for watchlist
  const convertBaseAssetToTracked = (ba: BaseAsset): TrackedAsset => {
    const isCrypto = ba.asset_type === "crypto";
    const isFund = ba.asset_type === "mutual_fund";
    const isCommodity = ba.asset_type === "commodity";

    let iconBg = "bg-[#818cf8]/20 text-[#818cf8]";
    if (isCrypto) iconBg = "bg-amber-500/20 text-amber-400";
    if (isFund) iconBg = "bg-emerald-500/20 text-emerald-400";
    if (isCommodity) iconBg = "bg-yellow-500/20 text-yellow-400";

    const forecastTarget = ba.current_price * (1 + (ba.change_24h_pct >= 0 ? 0.08 : -0.05));
    const potentialPct = ((forecastTarget - ba.current_price) / ba.current_price) * 100;

    return {
      symbol: ba.symbol,
      name: ba.name,
      category: `${ba.asset_type.replace("_", " ").toUpperCase()} • ${ba.currency}`,
      price: ba.current_price,
      change1d: ba.change_24h_pct,
      forecast30d: forecastTarget,
      potential: potentialPct,
      accuracy: 85.00,
      risk: Math.abs(ba.change_24h_pct) > 2.5 ? "High" : isCrypto ? "Medium" : "Low",
      iconText: ba.symbol.slice(0, 2),
      iconBg,
    };
  };

  // Filter watchlist items
  const filteredWatchlist = watchlist.filter((item) => {
    const matchesFilter = activeFilter === "all" || item.risk.toLowerCase() === activeFilter.toLowerCase();
    const matchesSearch =
      item.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  // Filter backend catalog for Add Asset modal search
  const filteredCatalog = fullCatalog
    .map(convertBaseAssetToTracked)
    .filter(
      (item) =>
        item.symbol.toLowerCase().includes(addSearchQuery.toLowerCase()) ||
        item.name.toLowerCase().includes(addSearchQuery.toLowerCase())
    );

  return (
    <div className="space-y-6 relative">
      {/* Toast Notification Banner */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 bg-[#818cf8] text-[#131e8c] px-4 py-2.5 rounded-xl font-mono font-bold text-xs shadow-2xl animate-bounce flex items-center gap-2 max-w-md">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      {/* Duplicate Asset Error Modal */}
      {errorModalMessage && (
        <div className="fixed inset-0 z-50 bg-[#0b1326]/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#171f33] border border-[#ff5c72]/50 w-full max-w-md rounded-2xl p-6 shadow-2xl space-y-4 text-center">
            <div className="h-12 w-12 rounded-2xl bg-[#ff5c72]/10 border border-[#ff5c72]/30 flex items-center justify-center mx-auto text-[#ffb2b7]">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#dae2fd]">Asset Already Added</h3>
              <p className="text-xs text-[#c6c5d5] mt-1.5 leading-relaxed">{errorModalMessage}</p>
            </div>
            <button
              onClick={() => setErrorModalMessage(null)}
              className="px-5 py-2 bg-[#818cf8] text-[#131e8c] font-bold text-xs rounded-xl shadow transition-all hover:opacity-90"
            >
              Understand & Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Set Price Alert Modal with Strict Logic Validation */}
      {alertingAsset && (
        <div className="fixed inset-0 z-50 bg-[#0b1326]/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#171f33] border border-[#2d3449] w-full max-w-md rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-[#2d3449]">
              <h3 className="text-sm font-bold text-[#dae2fd] flex items-center gap-2">
                <Bell className="h-4 w-4 text-amber-400" /> Set Price Alert ({alertingAsset.symbol})
              </h3>
              <button
                onClick={() => setAlertingAsset(null)}
                className="text-[#908f9e] hover:text-[#dae2fd] p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-[10px] text-[#908f9e] block mb-1">CURRENT PRICE</label>
                <div className="text-sm font-bold text-[#dae2fd]">{formatCurrency(alertingAsset.price)}</div>
              </div>

              <div>
                <label className="text-[10px] text-[#908f9e] block mb-1">TRIGGER CONDITION</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleSelectAlertCondition("Above")}
                    className={`flex-1 py-1.5 rounded-lg border font-bold text-xs transition-all ${
                      alertCondition === "Above"
                        ? "bg-[#4edea3]/10 text-[#4edea3] border-[#4edea3]/40"
                        : "bg-[#0b1326] text-[#908f9e] border-[#2d3449]"
                    }`}
                  >
                    Rises Above (&gt; {formatCurrency(alertingAsset.price)})
                  </button>
                  <button
                    onClick={() => handleSelectAlertCondition("Below")}
                    className={`flex-1 py-1.5 rounded-lg border font-bold text-xs transition-all ${
                      alertCondition === "Below"
                        ? "bg-[#ffb2b7]/10 text-[#ffb2b7] border-[#ffb2b7]/40"
                        : "bg-[#0b1326] text-[#908f9e] border-[#2d3449]"
                    }`}
                  >
                    Drops Below (&lt; {formatCurrency(alertingAsset.price)})
                  </button>
                </div>
              </div>

              <div>
                <label className="text-[10px] text-[#908f9e] block mb-1">TARGET THRESHOLD PRICE ($)</label>
                <input
                  type="number"
                  step="any"
                  value={alertPriceInput}
                  onChange={(e) => setAlertPriceInput(e.target.value)}
                  className="w-full bg-[#0b1326] text-[#dae2fd] text-xs font-bold rounded-xl px-3 py-2 border border-[#2d3449] focus:outline-none focus:border-[#818cf8]"
                />
                <p className="text-[10px] text-[#908f9e] mt-1">
                  {alertCondition === "Above"
                    ? `Must be greater than current price (${formatCurrency(alertingAsset.price)})`
                    : `Must be lower than current price (${formatCurrency(alertingAsset.price)})`}
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-[#2d3449]">
              <button
                onClick={() => setAlertingAsset(null)}
                className="px-4 py-2 bg-[#0b1326] text-[#908f9e] hover:text-[#dae2fd] text-xs font-semibold rounded-xl border border-[#2d3449]"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePriceAlert}
                className="px-4 py-2 bg-[#818cf8] text-[#131e8c] text-xs font-bold rounded-xl shadow hover:bg-[#818cf8]/90"
              >
                Save Price Alert
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#171f33] p-6 border border-[#2d3449] rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <div className="p-2 rounded-xl bg-[#818cf8]/10 text-[#818cf8] border border-[#818cf8]/20">
              <Bookmark className="h-5 w-5" />
            </div>
            <h1 className="text-xl font-bold text-[#dae2fd]">
              Watchlist Intelligence
            </h1>
          </div>
          <p className="text-xs text-[#908f9e]">
            Monitoring personalized assets and SarmayaSaaz AI forecast tracking metrics.
          </p>
        </div>

        <div className="flex gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search watchlist assets..."
              className="w-full bg-[#0b1326] text-[#dae2fd] placeholder-[#908f9e] text-xs rounded-xl pl-9 pr-3 py-2 border border-[#2d3449] focus:outline-none focus:border-[#818cf8]"
            />
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#908f9e]" />
          </div>
          {/* Functional Add Asset Button */}
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#818cf8] text-[#131e8c] font-semibold text-xs rounded-xl shadow hover:bg-[#818cf8]/90 transition-all shrink-0 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            <span>Add Asset</span>
          </button>
        </div>
      </div>

      {/* Add Asset Interactive Modal with Full Catalog Search */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#0b1326]/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#171f33] border border-[#2d3449] w-full max-w-lg rounded-2xl p-6 shadow-2xl space-y-4 relative">
            <div className="flex justify-between items-center pb-3 border-b border-[#2d3449]">
              <h3 className="text-sm font-bold text-[#dae2fd] flex items-center gap-2">
                <Plus className="h-4 w-4 text-[#818cf8]" /> Add Asset from Market Catalog
              </h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-[#908f9e] hover:text-[#dae2fd] p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="relative">
              <input
                type="text"
                value={addSearchQuery}
                onChange={(e) => setAddSearchQuery(e.target.value)}
                placeholder="Search all assets (Stocks, Crypto, Mutual Funds, Commodities)..."
                className="w-full bg-[#0b1326] text-[#dae2fd] placeholder-[#908f9e] text-xs rounded-xl pl-9 pr-3 py-2 border border-[#2d3449] focus:outline-none focus:border-[#818cf8]"
              />
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#908f9e]" />
            </div>

            <div className="space-y-2 max-h-72 overflow-y-auto divide-y divide-[#2d3449] pr-1">
              {filteredCatalog.length === 0 ? (
                <div className="p-4 text-center text-[#908f9e] text-xs font-mono">
                  No matching assets found in catalog
                </div>
              ) : (
                filteredCatalog.map((item) => {
                  const isTracked = watchlist.some((w) => w.symbol.toUpperCase() === item.symbol.toUpperCase());
                  return (
                    <div
                      key={item.symbol}
                      className="pt-2 flex items-center justify-between font-mono text-xs"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-[#dae2fd]">{item.name}</span>
                          <span className="text-[#818cf8] font-bold">({item.symbol})</span>
                        </div>
                        <span className="text-[10px] text-[#908f9e] font-sans">{item.category}</span>
                      </div>
                      <button
                        onClick={() => handleAddAsset(item)}
                        disabled={isTracked}
                        className={`px-3 py-1 rounded-lg text-xs font-bold transition-all border ${
                          isTracked
                            ? "bg-[#0b1326] text-[#908f9e] border-[#2d3449] cursor-not-allowed"
                            : "bg-[#818cf8]/10 text-[#818cf8] hover:bg-[#818cf8] hover:text-[#131e8c] border-[#818cf8]/30"
                        }`}
                      >
                        {isTracked ? "Tracked" : "+ Add"}
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* Top Summary Bento Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Strongest Bull Forecast */}
        <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl flex flex-col justify-between relative overflow-hidden">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-[#4edea3] flex items-center gap-1">
                <Zap className="h-4 w-4" /> Strongest Bull Forecast
              </span>
            </div>
            <h3 className="font-bold text-lg text-[#dae2fd] mt-1">NVIDIA (NVDA)</h3>
            <p className="text-xs text-[#908f9e]">Technology • Semiconductors</p>
          </div>

          <div className="mt-6 flex items-end justify-between">
            <div>
              <p className="text-[10px] font-mono text-[#908f9e]">Target (30D)</p>
              <p className="text-xl font-mono font-bold text-[#4edea3]">
                {formatCurrency(1150.20)}
              </p>
            </div>
            <div className="bg-[#4edea3]/10 px-2.5 py-1 rounded-lg text-[#4edea3] font-mono text-xs font-bold border border-[#4edea3]/20 flex items-center gap-1">
              <TrendingUp className="h-3.5 w-3.5" />
              {formatPercent(18.07, 2, true)}
            </div>
          </div>
        </div>

        {/* Highest Model Accuracy */}
        <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-[#818cf8] flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" /> Highest Model Accuracy
              </span>
            </div>
            <h3 className="font-bold text-lg text-[#dae2fd] mt-1">Gold (XAU/USD)</h3>
            <p className="text-xs text-[#908f9e]">Commodities • Precious Metals</p>
          </div>

          <div className="mt-6 flex items-end justify-between">
            <div>
              <p className="text-[10px] font-mono text-[#908f9e]">Accuracy Score</p>
              <p className="text-xl font-mono font-bold text-[#818cf8]">
                {formatPercent(94.20)}
              </p>
            </div>
            <div className="text-[11px] font-mono text-[#908f9e] text-right">
              Last 30 Predictions
            </div>
          </div>
        </div>

        {/* Active Volatility Alerts */}
        <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl flex flex-col justify-between border-l-4 border-l-[#ff5c72]">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-[#ffb2b7] flex items-center gap-1">
                <AlertTriangle className="h-4 w-4" /> Active Risk Updates
              </span>
            </div>
            <h3 className="font-bold text-lg text-[#dae2fd] mt-1">2 Active Signals</h3>
          </div>

          <div className="mt-4 space-y-2 text-xs font-mono">
            <div className="bg-[#0b1326] p-2 rounded-lg border border-[#2d3449] text-[#908f9e] truncate">
              BTC risk rating adjusted to High Volatility
            </div>
            <div className="bg-[#0b1326] p-2 rounded-lg border border-[#2d3449] text-[#908f9e] truncate">
              NVDA forecast target revised upward by PatchTST
            </div>
          </div>
        </div>
      </div>

      {/* Main Tracked Assets Table */}
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-[#2d3449]">
          <h2 className="text-xs font-bold text-[#dae2fd] uppercase tracking-wider">
            Tracked Watchlist Assets ({filteredWatchlist.length})
          </h2>

          <div className="flex items-center gap-2">
            {["all", "low", "medium", "high"].map((flt) => (
              <button
                key={flt}
                onClick={() => setActiveFilter(flt)}
                className={`px-3 py-1 text-xs font-mono rounded-lg uppercase transition-all ${
                  activeFilter === flt
                    ? "bg-[#818cf8] text-[#131e8c] font-bold"
                    : "bg-[#0b1326] text-[#908f9e] hover:text-[#dae2fd] border border-[#2d3449]"
                }`}
              >
                {flt}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b border-[#2d3449] text-[#908f9e] text-[10px]">
                <th className="py-3 px-3">ASSET</th>
                <th className="py-3 px-3 text-right">CURRENT PRICE</th>
                <th className="py-3 px-3 text-right">1D CHANGE</th>
                <th className="py-3 px-3 text-right">30D FORECAST</th>
                <th className="py-3 px-3 text-right">POTENTIAL</th>
                <th className="py-3 px-3 text-center">ACCURACY</th>
                <th className="py-3 px-3 text-center">RISK / ALERTS</th>
                <th className="py-3 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3449]">
              {filteredWatchlist.map((asset) => {
                const isPos1d = asset.change1d >= 0;
                const isPosPot = asset.potential >= 0;
                const isMenuOpen = activeRowAction === asset.symbol;

                return (
                  <tr key={asset.symbol} className="hover:bg-[#131b2e]/50 transition-colors relative">
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${asset.iconBg}`}>
                          {asset.iconText}
                        </div>
                        <div>
                          <div className="font-bold text-[#dae2fd] text-sm font-sans">{asset.symbol}</div>
                          <div className="text-[10px] text-[#908f9e] font-sans">{asset.name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-right font-bold text-[#dae2fd] text-sm">
                      {formatCurrency(asset.price)}
                    </td>
                    <td className={`py-3 px-3 text-right font-bold ${isPos1d ? "text-[#4edea3]" : "text-[#ffb2b7]"}`}>
                      {formatPercent(asset.change1d, 2, true)}
                    </td>
                    <td className="py-3 px-3 text-right font-bold text-[#dae2fd]">
                      {formatCurrency(asset.forecast30d)}
                    </td>
                    <td className={`py-3 px-3 text-right font-bold ${isPosPot ? "text-[#4edea3]" : "text-[#ffb2b7]"}`}>
                      {formatPercent(asset.potential, 2, true)}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span className="inline-flex items-center gap-1 bg-[#0b1326] px-2 py-0.5 rounded text-[#818cf8] border border-[#818cf8]/20 text-[11px]">
                        <Target className="h-3 w-3" /> {formatPercent(asset.accuracy)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center">
                      <div className="flex flex-col items-center gap-1">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                            asset.risk === "High"
                              ? "bg-[#ff5c72]/10 text-[#ffb2b7] border-[#ff5c72]/30"
                              : asset.risk === "Medium"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              : "bg-[#4edea3]/10 text-[#4edea3] border-[#4edea3]/30"
                          }`}
                        >
                          {asset.risk}
                        </span>
                        {asset.activeAlert && (
                          <span className="text-[9px] text-amber-400 font-bold flex items-center gap-0.5">
                            <Bell className="h-2.5 w-2.5" />
                            {asset.activeAlert.condition} {formatCurrency(asset.activeAlert.targetPrice)}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-3 text-right relative">
                      {/* Functional Row Action Dropdown */}
                      <button
                        onClick={() => setActiveRowAction(isMenuOpen ? null : asset.symbol)}
                        className="p-1.5 rounded-lg bg-[#0b1326] border border-[#2d3449] text-[#908f9e] hover:text-[#dae2fd] hover:border-[#818cf8]/40 transition-all"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </button>

                      {isMenuOpen && (
                        <div className="absolute right-3 top-10 w-52 bg-[#131b2e] border border-[#2d3449] rounded-xl shadow-2xl z-40 py-1 text-left font-sans text-xs space-y-0.5 divide-y divide-[#2d3449]">
                          <button
                            onClick={() => router.push(`/?symbol=${asset.symbol}`)}
                            className="w-full px-3 py-2 flex items-center gap-2 hover:bg-[#171f33] text-[#dae2fd]"
                          >
                            <ExternalLink className="h-3.5 w-3.5 text-[#818cf8]" />
                            <span>View AI Forecast</span>
                          </button>
                          
                          <button
                            onClick={() => handleOpenPriceAlertModal(asset)}
                            className="w-full px-3 py-2 flex items-center gap-2 hover:bg-[#171f33] text-[#dae2fd]"
                          >
                            <Bell className="h-3.5 w-3.5 text-amber-400" />
                            <span>{asset.activeAlert ? "Edit Price Alert" : "Set Price Alert"}</span>
                          </button>

                          {/* Functional Remove Price Alert Button for Assets with Active Alerts */}
                          {asset.activeAlert && (
                            <button
                              onClick={() => handleRemovePriceAlert(asset.symbol)}
                              className="w-full px-3 py-2 flex items-center gap-2 hover:bg-amber-500/10 text-amber-400"
                            >
                              <BellOff className="h-3.5 w-3.5 text-amber-400" />
                              <span>Remove Price Alert</span>
                            </button>
                          )}

                          <button
                            onClick={() => handleRemoveAsset(asset.symbol)}
                            className="w-full px-3 py-2 flex items-center gap-2 hover:bg-[#ff5c72]/10 text-[#ffb2b7]"
                          >
                            <Trash2 className="h-3.5 w-3.5 text-[#ffb2b7]" />
                            <span>Remove Item</span>
                          </button>
                        </div>
                      )}
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
