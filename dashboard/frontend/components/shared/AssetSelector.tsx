"use client";

import React, { useState } from "react";
import { BaseAsset, AssetType } from "@/lib/api/types";
import { ChevronDown, Coins, LineChart, PieChart, Shield } from "lucide-react";

interface AssetSelectorProps {
  assets: BaseAsset[];
  selectedAsset: BaseAsset;
  onSelectAsset: (asset: BaseAsset) => void;
}

export const AssetSelector: React.FC<AssetSelectorProps> = ({
  assets,
  selectedAsset,
  onSelectAsset,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("all");

  const tabs = [
    { id: "all", label: "All Assets" },
    { id: "crypto", label: "Crypto" },
    { id: "stock", label: "Stocks" },
    { id: "mutual_fund", label: "Mutual Funds" },
    { id: "commodity", label: "Commodities" },
  ];

  const filteredAssets =
    activeTab === "all"
      ? assets
      : assets.filter((a) => a.asset_type === activeTab);

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2 bg-[#171f33] hover:bg-[#222a3d] border border-[#334155] rounded-xl text-[#dae2fd] shadow-md transition-all"
      >
        <div className="flex flex-col text-left">
          <div className="flex items-center gap-2">
            <span className="font-bold text-base">{selectedAsset.name}</span>
            <span className="text-xs px-2 py-0.5 rounded bg-[#818cf8]/10 text-[#bdc2ff] font-mono border border-[#818cf8]/20">
              {selectedAsset.symbol}
            </span>
          </div>
          <span className="text-[11px] text-[#908f9e] uppercase font-mono tracking-wider">
            {selectedAsset.asset_type.replace("_", " ")}
          </span>
        </div>
        <ChevronDown className="h-4 w-4 text-[#908f9e] ml-2" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-80 bg-[#131b2e] border border-[#334155] rounded-xl shadow-2xl z-50 p-3">
          {/* Asset Type Tabs */}
          <div className="flex gap-1 overflow-x-auto pb-2 mb-2 border-b border-[#2d3449]">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-2.5 py-1 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? "bg-[#818cf8] text-[#131e8c] font-semibold"
                    : "text-[#c6c5d5] hover:bg-[#171f33]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Asset List */}
          <div className="max-h-64 overflow-y-auto space-y-1">
            {filteredAssets.map((asset) => (
              <div
                key={asset.symbol}
                onClick={() => {
                  onSelectAsset(asset);
                  setIsOpen(false);
                }}
                className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                  selectedAsset.symbol === asset.symbol
                    ? "bg-[#222a3d] border border-[#818cf8]/30"
                    : "hover:bg-[#171f33]"
                }`}
              >
                <div className="flex flex-col">
                  <span className="font-semibold text-xs text-[#dae2fd]">
                    {asset.name}
                  </span>
                  <span className="text-[10px] text-[#908f9e] font-mono">
                    {asset.symbol}
                  </span>
                </div>
                <div className="flex flex-col text-right">
                  <span className="font-mono text-xs text-[#dae2fd]">
                    ${asset.current_price.toLocaleString()}
                  </span>
                  <span
                    className={`text-[10px] font-mono ${
                      asset.change_24h_pct >= 0
                        ? "text-[#4edea3]"
                        : "text-[#ffb2b7]"
                    }`}
                  >
                    {asset.change_24h_pct >= 0 ? "+" : ""}
                    {asset.change_24h_pct}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
