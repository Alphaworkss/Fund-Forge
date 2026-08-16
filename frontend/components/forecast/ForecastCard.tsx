"use client";

import React from "react";
import { ForecastResponse } from "@/lib/api/types";
import { TrendingUp, TrendingDown, Target, ShieldCheck } from "lucide-react";
import { formatCurrency, formatPercent } from "@/lib/formatters";

interface ForecastCardProps {
  forecast?: ForecastResponse;
}

export const ForecastCard: React.FC<ForecastCardProps> = ({ forecast }) => {
  if (!forecast) return null;

  const isBullish = forecast.direction === "bullish";
  const confidencePct = forecast.confidence * 100;

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#2d3449]">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-[#818cf8]" />
          <h3 className="font-semibold text-base text-[#dae2fd]">
            {forecast.horizon.toUpperCase()} AI Target Forecast
          </h3>
        </div>
        <span
          className={`flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full uppercase ${
            isBullish
              ? "bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30"
              : "bg-[#ffb2b7]/10 text-[#ffb2b7] border border-[#ffb2b7]/30"
          }`}
        >
          {isBullish ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
          {forecast.direction}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4 font-mono text-center">
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[10px] text-[#908f9e] block">LOWER BOUND</span>
          <span className="text-sm font-bold text-[#ffb2b7]">
            {formatCurrency(forecast.lower_bound)}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#818cf8]/40 shadow-lg shadow-[#818cf8]/5">
          <span className="text-[10px] text-[#818cf8] block font-bold">EXPECTED TARGET</span>
          <span className="text-base font-bold text-[#dae2fd]">
            {formatCurrency(forecast.central_estimate)}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[10px] text-[#908f9e] block">UPPER BOUND</span>
          <span className="text-sm font-bold text-[#4edea3]">
            {formatCurrency(forecast.upper_bound)}
          </span>
        </div>
      </div>

      {/* Confidence Indicator */}
      <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449] flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-[#818cf8]" />
          <span className="text-[#c6c5d5]">Model Confidence</span>
        </div>
        <div className="flex items-center gap-2 font-mono font-bold">
          <span className="text-[#818cf8]">{formatPercent(confidencePct)}</span>
          <div className="w-20 h-2 bg-[#131b2e] rounded-full overflow-hidden">
            <div
              style={{ width: `${Math.min(100, Math.max(0, confidencePct))}%` }}
              className="h-full bg-[#818cf8] rounded-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
