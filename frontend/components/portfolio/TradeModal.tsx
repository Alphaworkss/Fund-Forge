"use client";

import React, { useState } from "react";
import { BaseAsset } from "@/lib/api/types";
import { ApiService } from "@/lib/api/services";
import { X, TrendingUp, TrendingDown, RefreshCw } from "lucide-react";

interface TradeModalProps {
  assets: BaseAsset[];
  initialAsset?: BaseAsset;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const TradeModal: React.FC<TradeModalProps> = ({
  assets,
  initialAsset,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [selectedSymbol, setSelectedSymbol] = useState(
    initialAsset?.symbol || assets[0]?.symbol || "BTC"
  );
  const [action, setAction] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const currentAsset = assets.find((a) => a.symbol === selectedSymbol) || assets[0];
  const estTotal = (quantity || 0) * (currentAsset?.current_price || 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await ApiService.executeTrade({
        symbol: selectedSymbol,
        action,
        quantity: Number(quantity),
      });
      setLoading(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to execute order");
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#131b2e] border border-[#334155] rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#908f9e] hover:text-[#dae2fd] transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <h3 className="text-lg font-bold text-[#dae2fd] mb-4">
          Execute Paper Trade Order
        </h3>

        {error && (
          <div className="mb-4 p-3 bg-[#ffb4ab]/10 border border-[#ffb4ab]/30 rounded-xl text-[#ffb4ab] text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
          {/* Action Tabs: BUY / SELL */}
          <div className="grid grid-cols-2 gap-2 p-1 bg-[#0b1326] rounded-xl border border-[#2d3449]">
            <button
              type="button"
              onClick={() => setAction("buy")}
              className={`py-2 rounded-lg font-bold text-xs transition-all ${
                action === "buy"
                  ? "bg-[#4edea3] text-[#003824] shadow"
                  : "text-[#c6c5d5] hover:text-[#dae2fd]"
              }`}
            >
              BUY / SUBSCRIBE
            </button>
            <button
              type="button"
              onClick={() => setAction("sell")}
              className={`py-2 rounded-lg font-bold text-xs transition-all ${
                action === "sell"
                  ? "bg-[#ffb2b7] text-[#67001b] shadow"
                  : "text-[#c6c5d5] hover:text-[#dae2fd]"
              }`}
            >
              SELL / REDEEM
            </button>
          </div>

          {/* Asset Selection */}
          <div>
            <label className="block text-[#908f9e] text-[10px] mb-1">SELECT ASSET</label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full bg-[#0b1326] text-[#dae2fd] border border-[#2d3449] rounded-xl p-2.5 text-xs focus:border-[#818cf8] focus:outline-none"
            >
              {assets.map((a) => (
                <option key={a.symbol} value={a.symbol}>
                  {a.name} ({a.symbol}) — ${a.current_price.toLocaleString()} [{a.asset_type.toUpperCase()}]
                </option>
              ))}
            </select>
          </div>

          {/* Quantity Input */}
          <div>
            <label className="block text-[#908f9e] text-[10px] mb-1">QUANTITY ({currentAsset?.unit})</label>
            <input
              type="number"
              step="any"
              min="0.001"
              value={quantity}
              onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
              className="w-full bg-[#0b1326] text-[#dae2fd] border border-[#2d3449] rounded-xl p-2.5 text-xs focus:border-[#818cf8] focus:outline-none font-mono"
            />
          </div>

          {/* Estimated Cost Summary */}
          <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449] space-y-1">
            <div className="flex justify-between text-[#c6c5d5]">
              <span>Execution Price:</span>
              <span className="font-bold text-[#dae2fd]">
                ${currentAsset?.current_price.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-[#c6c5d5] pt-1 border-t border-[#2d3449]">
              <span className="font-bold">Total Estimated Value:</span>
              <span className="font-bold text-[#818cf8] text-sm">
                ${estTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-xl font-bold text-xs shadow-lg transition-all flex items-center justify-center gap-2 ${
              action === "buy"
                ? "bg-[#4edea3] hover:bg-[#4edea3]/90 text-[#003824]"
                : "bg-[#ffb2b7] hover:bg-[#ffb2b7]/90 text-[#67001b]"
            }`}
          >
            {loading && <RefreshCw className="h-4 w-4 animate-spin" />}
            <span>
              Confirm {action.toUpperCase()} Order ({selectedSymbol})
            </span>
          </button>
        </form>
      </div>
    </div>
  );
};
