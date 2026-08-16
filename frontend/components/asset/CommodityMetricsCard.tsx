"use client";

import React from "react";
import { BaseAsset } from "@/lib/api/types";
import { Layers } from "lucide-react";
import { formatNumber } from "@/lib/formatters";

interface Props {
  asset: BaseAsset;
}

export const CommodityMetricsCard: React.FC<Props> = ({ asset }) => {
  const meta = asset.metadata || {};

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#2d3449]">
        <Layers className="h-4 w-4 text-[#818cf8]" />
        <h3 className="font-semibold text-base text-[#dae2fd]">Commodity Contract Specs</h3>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">TRADING UNIT</span>
          <span className="text-[#dae2fd] font-bold text-sm">{asset.unit}</span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">CONTRACT TYPE</span>
          <span className="text-[#dae2fd] font-bold text-sm">{meta.contract_type}</span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">CONTRACT MONTH</span>
          <span className="text-[#818cf8] font-bold text-sm">{meta.contract_month || "Spot"}</span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">OPEN INTEREST</span>
          <span className="text-[#4edea3] font-bold text-sm">
            {meta.open_interest ? formatNumber(meta.open_interest, 2) : "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
};
