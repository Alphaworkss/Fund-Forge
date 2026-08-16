"use client";

import React from "react";
import { BaseAsset } from "@/lib/api/types";
import { Building2 } from "lucide-react";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/formatters";

interface Props {
  asset: BaseAsset;
}

export const StockFundamentalsCard: React.FC<Props> = ({ asset }) => {
  const meta = asset.metadata || {};

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#2d3449]">
        <Building2 className="h-4 w-4 text-[#818cf8]" />
        <h3 className="font-semibold text-base text-[#dae2fd]">Stock Fundamentals</h3>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">MARKET CAP</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            ${formatNumber(meta.market_cap ? meta.market_cap / 1e9 : 0)}B
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">P/E RATIO</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            {meta.pe_ratio ? `${formatNumber(meta.pe_ratio)}x` : "N/A"}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">EPS</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            {meta.eps ? formatCurrency(meta.eps) : "N/A"}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">DIVIDEND YIELD</span>
          <span className="text-[#4edea3] font-bold text-sm">
            {formatPercent(meta.dividend_yield || 0)}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">52W HIGH</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            {formatCurrency(meta.fifty_two_week_high || 0)}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">52W LOW</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            {formatCurrency(meta.fifty_two_week_low || 0)}
          </span>
        </div>
      </div>
    </div>
  );
};
