"use client";

import React from "react";
import { BaseAsset } from "@/lib/api/types";
import { Coins } from "lucide-react";
import { formatNumber, formatPercent } from "@/lib/formatters";

interface Props {
  asset: BaseAsset;
}

export const CryptoMetricsCard: React.FC<Props> = ({ asset }) => {
  const meta = asset.metadata || {};

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#2d3449]">
        <Coins className="h-4 w-4 text-[#818cf8]" />
        <h3 className="font-semibold text-base text-[#dae2fd]">Crypto Network & Supply</h3>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">MARKET CAP</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            ${formatNumber(meta.market_cap ? meta.market_cap / 1e9 : 0)}B
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">24H VOLUME</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            ${formatNumber(meta.volume_24h ? meta.volume_24h / 1e9 : 0)}B
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">CIRCULATING SUPPLY</span>
          <span className="text-[#dae2fd] font-bold text-sm">
            {formatNumber(meta.circulating_supply || 0, 2)} {asset.symbol}
          </span>
        </div>
        <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449]">
          <span className="text-[#908f9e] text-[10px] block">BTC DOMINANCE</span>
          <span className="text-[#818cf8] font-bold text-sm">
            {meta.btc_dominance_percent ? formatPercent(meta.btc_dominance_percent) : "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
};
