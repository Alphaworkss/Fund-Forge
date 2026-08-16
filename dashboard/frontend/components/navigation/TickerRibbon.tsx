"use client";

import React, { useEffect, useState } from "react";
import { ApiService } from "@/lib/api/services";
import { BaseAsset } from "@/lib/api/types";
import { formatCurrency, formatPercent } from "@/lib/formatters";

export const TickerRibbon: React.FC = () => {
  const [assets, setAssets] = useState<BaseAsset[]>([]);

  useEffect(() => {
    ApiService.getAssets()
      .then((res) => {
        // Sort assets by max price gain percentage (highest gainers first)
        const sorted = [...res.assets].sort((a, b) => b.change_24h_pct - a.change_24h_pct);
        setAssets(sorted);
      })
      .catch((err) => console.error("Failed to load ticker assets", err));
  }, []);

  if (assets.length === 0) return null;

  return (
    <div className="ticker-wrap top-16 fixed left-0 w-full z-40 h-8 flex items-center bg-[#0b1326] border-b border-[#2d3449]">
      <div className="ticker flex items-center">
        {assets.concat(assets).map((asset, idx) => {
          const isPositive = asset.change_24h_pct >= 0;
          return (
            <div key={`${asset.symbol}-${idx}`} className="ticker-item flex items-center gap-2">
              <span className="font-semibold text-xs text-[#dae2fd]">{asset.symbol}</span>
              <span className="font-mono text-xs text-[#c6c5d5]">
                {formatCurrency(asset.current_price)}
              </span>
              <span
                className={`flex items-center text-[11px] font-mono font-medium ${
                  isPositive ? "text-[#4edea3]" : "text-[#ffb2b7]"
                }`}
              >
                {formatPercent(asset.change_24h_pct, 2, true)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
