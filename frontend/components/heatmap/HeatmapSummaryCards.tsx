"use client";

import React from "react";
import { Cpu, Award, Zap, Layers } from "lucide-react";
import { formatPercent, formatNumber } from "@/lib/formatters";

interface HeatmapSummaryCardsProps {
  bestModel: string;
  bestAssetClass: string;
  bestAsset: string;
  bestAssetScore: number;
  totalAssetsCount: number;
}

export const HeatmapSummaryCards: React.FC<HeatmapSummaryCardsProps> = ({
  bestModel,
  bestAssetClass,
  bestAsset,
  bestAssetScore,
  totalAssetsCount,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Best Overall Model */}
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-4 shadow-xl flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono font-bold text-[#908f9e] uppercase tracking-wider block mb-1">
            Best Overall Model
          </span>
          <h3 className="text-lg font-bold text-[#dae2fd]">{bestModel}</h3>
          <p className="text-[11px] font-mono text-[#818cf8] mt-0.5">Top Median Score</p>
        </div>
        <div className="p-3 rounded-2xl bg-[#818cf8]/10 text-[#818cf8] border border-[#818cf8]/20">
          <Cpu className="h-6 w-6" />
        </div>
      </div>

      {/* Best Asset Class */}
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-4 shadow-xl flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono font-bold text-[#908f9e] uppercase tracking-wider block mb-1">
            Best Asset Class
          </span>
          <h3 className="text-lg font-bold text-[#4edea3]">{bestAssetClass}</h3>
          <p className="text-[11px] font-mono text-[#908f9e] mt-0.5">Highest Predictability</p>
        </div>
        <div className="p-3 rounded-2xl bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/20">
          <Layers className="h-6 w-6" />
        </div>
      </div>

      {/* Best Performing Asset */}
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-4 shadow-xl flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono font-bold text-[#908f9e] uppercase tracking-wider block mb-1">
            Top Performing Asset
          </span>
          <h3 className="text-lg font-bold text-[#dae2fd]">{bestAsset}</h3>
          <p className="text-[11px] font-mono text-[#4edea3] font-bold mt-0.5">
            Score: {formatNumber(bestAssetScore)} / 100.00
          </p>
        </div>
        <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Award className="h-6 w-6" />
        </div>
      </div>

      {/* Assets Evaluated */}
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-4 shadow-xl flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono font-bold text-[#908f9e] uppercase tracking-wider block mb-1">
            Assets Evaluated
          </span>
          <h3 className="text-lg font-bold text-[#dae2fd]">{totalAssetsCount} Assets</h3>
          <p className="text-[11px] font-mono text-[#818cf8] mt-0.5">Across 4 Asset Classes</p>
        </div>
        <div className="p-3 rounded-2xl bg-[#818cf8]/10 text-[#818cf8] border border-[#818cf8]/20">
          <Zap className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
};
