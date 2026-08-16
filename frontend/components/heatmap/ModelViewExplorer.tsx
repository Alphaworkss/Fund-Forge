"use client";

import React, { useState } from "react";
import {
  ModelName,
  AVAILABLE_MODELS,
  AssetClassGroup,
  MetricType,
  METRIC_DEFINITIONS,
  HorizonType,
  AssetHeatmapEntry,
  CellMetrics,
} from "@/lib/heatmapData";
import { formatCurrency, formatPercent, formatNumber } from "@/lib/formatters";
import { Cpu, ChevronDown, ChevronRight, Layers, ArrowUpRight } from "lucide-react";
import { useRouter } from "next/navigation";

interface ModelViewExplorerProps {
  data: AssetClassGroup[];
  selectedMetric: MetricType;
  selectedHorizon: HorizonType;
  onSelectCell: (
    asset: AssetHeatmapEntry,
    model: ModelName,
    metrics: CellMetrics | null
  ) => void;
}

export const ModelViewExplorer: React.FC<ModelViewExplorerProps> = ({
  data,
  selectedMetric,
  selectedHorizon,
  onSelectCell,
}) => {
  const router = useRouter();
  const [activeModel, setActiveModel] = useState<ModelName>("XGBoost");
  const [expandedAssetClasses, setExpandedAssetClasses] = useState<Record<string, boolean>>({
    crypto: true,
    stock: true,
    mutual_fund: false,
    commodity: false,
  });

  const toggleExpand = (id: string) => {
    setExpandedAssetClasses((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Compute Median Score for selected model per Asset Class
  const getAssetClassMedianScore = (acGroup: AssetClassGroup): number => {
    const scores: number[] = [];
    acGroup.categories.forEach((cat) => {
      cat.assets.forEach((ast) => {
        const m = ast.models[activeModel][selectedHorizon];
        if (m && m.isAvailable) {
          scores.push(m[selectedMetric]);
        }
      });
    });

    if (scores.length === 0) return 0;
    scores.sort((a, b) => a - b);
    const mid = Math.floor(scores.length / 2);
    return scores.length % 2 !== 0 ? scores[mid] : (scores[mid - 1] + scores[mid]) / 2;
  };

  return (
    <div className="space-y-6">
      {/* Model Selection Bar */}
      <div className="bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl shadow-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-sm font-bold text-[#dae2fd] uppercase tracking-wider flex items-center gap-2">
            <Cpu className="h-4 w-4 text-[#818cf8]" /> Explore Performance by Model
          </h2>
          <p className="text-xs text-[#908f9e] mt-0.5">
            Evaluate how a single AI model performs across the entire multi-asset financial universe.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {AVAILABLE_MODELS.map((m) => (
            <button
              key={m}
              onClick={() => setActiveModel(m)}
              className={`px-3.5 py-1.5 rounded-xl font-mono text-xs font-bold transition-all ${
                activeModel === m
                  ? "bg-[#818cf8] text-[#131e8c] shadow"
                  : "bg-[#0b1326] text-[#c6c5d5] hover:text-[#dae2fd] border border-[#2d3449]"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Model Summary Breakdown Card */}
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-[#2d3449]">
          <h3 className="text-xs font-bold text-[#dae2fd] uppercase tracking-wider">
            {activeModel} — Median Performance Breakdown ({selectedHorizon.toUpperCase()})
          </h3>
          <span className="text-xs text-[#818cf8] font-mono font-bold">
            Metric: {METRIC_DEFINITIONS[selectedMetric].label}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
          {data.map((acGroup) => {
            const medianScore = getAssetClassMedianScore(acGroup);
            return (
              <div
                key={acGroup.id}
                className="bg-[#0b1326] p-4 rounded-xl border border-[#2d3449] flex items-center justify-between"
              >
                <div>
                  <span className="text-[10px] text-[#908f9e] block font-sans">{acGroup.name}</span>
                  <span className="text-lg font-bold text-[#4edea3]">
                    {formatNumber(medianScore)}
                  </span>
                </div>
                <div className="w-16 bg-[#131b2e] h-2 rounded-full overflow-hidden border border-[#2d3449]">
                  <div
                    className="bg-[#4edea3] h-full"
                    style={{ width: `${Math.min(100, medianScore)}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Expandable Asset Class Tree */}
      <div className="space-y-4">
        {data.map((acGroup) => {
          const isExpanded = expandedAssetClasses[acGroup.id];
          return (
            <div key={acGroup.id} className="bg-[#171f33] border border-[#2d3449] rounded-2xl shadow-xl overflow-hidden">
              <button
                onClick={() => toggleExpand(acGroup.id)}
                className="w-full p-4 flex items-center justify-between bg-[#171f33] hover:bg-[#131b2e]/50 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className="h-5 w-5 text-[#818cf8]" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-[#908f9e]" />
                  )}
                  <Layers className="h-4 w-4 text-[#818cf8]" />
                  <span className="font-bold text-sm text-[#dae2fd]">{acGroup.name}</span>
                  <span className="text-xs font-mono text-[#908f9e]">
                    ({acGroup.categories.reduce((acc, c) => acc + c.assets.length, 0)} assets)
                  </span>
                </div>

                <div className="text-xs font-mono font-bold text-[#4edea3]">
                  Median: {formatNumber(getAssetClassMedianScore(acGroup))}
                </div>
              </button>

              {isExpanded && (
                <div className="p-5 pt-0 border-t border-[#2d3449] space-y-4 font-mono text-xs">
                  {acGroup.categories.map((cat) => (
                    <div key={cat.id} className="space-y-2 pt-3">
                      <div className="text-[11px] font-bold text-[#818cf8] uppercase tracking-wider font-sans">
                        ▸ {cat.name} ({cat.assets.length})
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {cat.assets.map((asset) => {
                          const m = asset.models[activeModel][selectedHorizon];
                          const score = m ? m.overall_score : null;

                          return (
                            <div
                              key={asset.symbol}
                              onClick={() => onSelectCell(asset, activeModel, m)}
                              className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449] hover:border-[#818cf8]/60 transition-all cursor-pointer flex items-center justify-between"
                            >
                              <div>
                                <div className="font-bold text-[#dae2fd] flex items-center gap-1.5">
                                  <span>{asset.symbol}</span>
                                  <span className="text-[10px] text-[#908f9e] font-sans truncate max-w-[100px]">
                                    {asset.name}
                                  </span>
                                </div>
                                <div className="text-[10px] text-[#908f9e]">
                                  {formatCurrency(asset.currentPrice)}
                                </div>
                              </div>

                              <div className="flex items-center gap-2">
                                <span className="font-bold text-[#4edea3]">
                                  {score !== null ? formatNumber(score) : "N/A"}
                                </span>
                                <ArrowUpRight className="h-3.5 w-3.5 text-[#818cf8]" />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
