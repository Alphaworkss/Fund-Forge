"use client";

import React from "react";
import { BaseAsset } from "@/lib/api/types";
import { PieChart } from "lucide-react";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/formatters";

interface Props {
  asset: BaseAsset;
}

export const MutualFundMetricsCard: React.FC<Props> = ({ asset }) => {
  const meta = asset.metadata || {};

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#2d3449]">
        <PieChart className="h-4 w-4 text-[#818cf8]" />
        <h3 className="font-semibold text-base text-[#dae2fd]">Fund Structure & Allocation</h3>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs font-mono mb-4">
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">NET ASSET VALUE (NAV)</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            {formatCurrency(meta.nav)}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">AUM</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            ${formatNumber(meta.aum ? meta.aum / 1e9 : 0)}B
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">EXPENSE RATIO</span>
          <span className="text-[#4edea3] font-bold text-sm">
            {formatPercent(meta.expense_ratio || 0)}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">RISK LEVEL</span>
          <span className="text-[#818cf8] font-bold text-sm">{meta.risk_level}</span>
        </div>
      </div>

      {/* Asset Allocation Progress Bar */}
      <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
        <div className="flex justify-between text-[11px] mb-2 font-mono text-[#c6c5d5]">
          <span>Equity: {formatPercent(meta.equity_allocation_pct || 0)}</span>
          <span>Debt: {formatPercent(meta.debt_allocation_pct || 0)}</span>
          <span>Cash: {formatPercent(meta.cash_allocation_pct || 0)}</span>
        </div>
        <div className="h-2.5 w-full bg-[#131b2e] rounded-full overflow-hidden flex">
          <div style={{ width: `${meta.equity_allocation_pct || 0}%` }} className="bg-[#818cf8] h-full" />
          <div style={{ width: `${meta.debt_allocation_pct || 0}%` }} className="bg-[#4edea3] h-full" />
          <div style={{ width: `${meta.cash_allocation_pct || 0}%` }} className="bg-[#908f9e] h-full" />
        </div>
      </div>
    </div>
  );
};
