"use client";

import React from "react";
import {
  AssetHeatmapEntry,
  ModelName,
  AVAILABLE_MODELS,
  MetricType,
  METRIC_DEFINITIONS,
  HorizonType,
  CellMetrics,
} from "@/lib/heatmapData";
import { formatCurrency, formatPercent, formatNumber } from "@/lib/formatters";
import { Star } from "lucide-react";

interface HeatmapTableProps {
  assets: AssetHeatmapEntry[];
  selectedMetric: MetricType;
  selectedHorizon: HorizonType;
  onSelectCell: (
    asset: AssetHeatmapEntry,
    model: ModelName,
    metrics: CellMetrics | null
  ) => void;
}

export const HeatmapTable: React.FC<HeatmapTableProps> = ({
  assets,
  selectedMetric,
  selectedHorizon,
  onSelectCell,
}) => {
  const metricDef = METRIC_DEFINITIONS[selectedMetric];

  // Helper to extract metric value
  const getMetricValue = (metrics: CellMetrics | null): number | null => {
    if (!metrics || !metrics.isAvailable) return null;
    return metrics[selectedMetric];
  };

  // Format value for display
  const formatCellDisplay = (val: number | null): string => {
    if (val === null) return "N/A";
    if (selectedMetric === "overall_score" || selectedMetric === "r2_score") {
      return formatNumber(val);
    }
    if (selectedMetric === "directional_accuracy_pct" || selectedMetric === "mape_pct") {
      return formatPercent(val);
    }
    return formatCurrency(val);
  };

  // Find winning model per row
  const getWinningModel = (asset: AssetHeatmapEntry): ModelName | null => {
    let winning: ModelName | null = null;
    let bestVal: number | null = null;

    AVAILABLE_MODELS.forEach((m) => {
      const val = getMetricValue(asset.models[m][selectedHorizon]);
      if (val !== null) {
        if (bestVal === null) {
          bestVal = val;
          winning = m;
        } else if (metricDef.higherIsBetter ? val > bestVal : val < bestVal) {
          bestVal = val;
          winning = m;
        }
      }
    });

    return winning;
  };

  // Calculate color intensity (0 to 1) for heatmap gradient
  const getCellColorClass = (val: number | null, isBest: boolean): string => {
    if (val === null) {
      return "bg-[#0b1326]/40 text-[#908f9e] border-[#2d3449]";
    }

    if (isBest) {
      return "bg-[#4edea3]/20 text-[#4edea3] font-bold border-[#4edea3]/50 shadow-inner";
    }

    // High vs Low intensity
    if (selectedMetric === "overall_score" || selectedMetric === "directional_accuracy_pct" || selectedMetric === "r2_score") {
      if (val >= 85 || val >= 0.85) return "bg-[#818cf8]/25 text-[#dae2fd] border-[#818cf8]/30";
      if (val >= 75 || val >= 0.70) return "bg-[#818cf8]/15 text-[#c6c5d5] border-[#818cf8]/20";
      return "bg-[#ffb2b7]/10 text-[#ffb2b7] border-[#ffb2b7]/20";
    } else {
      // Lower is better metrics
      return "bg-[#818cf8]/15 text-[#dae2fd] border-[#818cf8]/20";
    }
  };

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl space-y-4">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse font-mono text-xs">
          <thead>
            <tr className="border-b border-[#2d3449] text-[#908f9e] text-[10px]">
              <th className="py-3 px-3">ASSET & TICKER</th>
              <th className="py-3 px-3">CATEGORY</th>
              <th className="py-3 px-3 text-right">PRICE</th>
              {AVAILABLE_MODELS.map((model) => (
                <th key={model} className="py-3 px-3 text-center min-w-[100px]">
                  {model}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#2d3449]">
            {assets.map((asset) => {
              const winningModel = getWinningModel(asset);

              return (
                <tr key={asset.symbol} className="hover:bg-[#131b2e]/50 transition-colors">
                  <td className="py-3 px-3">
                    <div className="flex flex-col">
                      <span className="font-bold text-[#dae2fd] text-sm font-sans">{asset.symbol}</span>
                      <span className="text-[10px] text-[#908f9e] font-sans truncate max-w-[130px]">
                        {asset.name}
                      </span>
                    </div>
                  </td>

                  <td className="py-3 px-3 text-[10px] text-[#908f9e] font-sans">
                    {asset.category}
                  </td>

                  <td className="py-3 px-3 text-right font-bold text-[#dae2fd]">
                    {formatCurrency(asset.currentPrice)}
                  </td>

                  {/* Heatmap Model Columns */}
                  {AVAILABLE_MODELS.map((m) => {
                    const metrics = asset.models[m][selectedHorizon];
                    const val = getMetricValue(metrics);
                    const isBest = winningModel === m && val !== null;
                    const colorClass = getCellColorClass(val, isBest);

                    return (
                      <td key={m} className="py-2 px-2 text-center">
                        <button
                          onClick={() => onSelectCell(asset, m, metrics)}
                          className={`w-full py-2.5 px-2 rounded-xl border text-xs font-bold transition-all relative group hover:scale-[1.03] ${colorClass}`}
                          title={`${asset.symbol} × ${m} (${selectedHorizon.toUpperCase()}): ${metricDef.label} = ${formatCellDisplay(val)}`}
                        >
                          <div className="flex items-center justify-center gap-1">
                            <span>{formatCellDisplay(val)}</span>
                            {isBest && (
                              <Star className="h-3 w-3 text-amber-400 fill-amber-400 shrink-0" />
                            )}
                          </div>

                          {/* Hover Tooltip */}
                          {metrics && metrics.isAvailable && (
                            <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-[#0b1326] border border-[#818cf8]/40 rounded-xl p-3 shadow-2xl z-50 text-left text-[10px] font-mono pointer-events-none divide-y divide-[#2d3449]">
                              <div className="pb-1 font-bold text-[#818cf8]">
                                {asset.symbol} × {m} ({selectedHorizon.toUpperCase()})
                              </div>
                              <div className="pt-1.5 space-y-1">
                                <div className="flex justify-between text-[#dae2fd]">
                                  <span>Score:</span>
                                  <span className="font-bold text-[#4edea3]">
                                    {formatNumber(metrics.overall_score)}
                                  </span>
                                </div>
                                <div className="flex justify-between text-[#908f9e]">
                                  <span>MAE:</span>
                                  <span>{formatCurrency(metrics.mae)}</span>
                                </div>
                                <div className="flex justify-between text-[#908f9e]">
                                  <span>R²:</span>
                                  <span>{formatNumber(metrics.r2_score)}</span>
                                </div>
                                <div className="flex justify-between text-[#908f9e]">
                                  <span>Direction:</span>
                                  <span>{formatPercent(metrics.directional_accuracy_pct)}</span>
                                </div>
                              </div>
                            </div>
                          )}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
