"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { X, ExternalLink, Cpu, Target, ArrowUpRight, BarChart2 } from "lucide-react";
import { CellMetrics, ModelName, HorizonType, METRIC_DEFINITIONS } from "@/lib/heatmapData";
import { formatCurrency, formatPercent, formatNumber } from "@/lib/formatters";

interface HeatmapCellDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
  assetName: string;
  assetClass: string;
  category: string;
  currentPrice: number;
  modelName: ModelName;
  horizon: HorizonType;
  metrics: CellMetrics | null;
}

export const HeatmapCellDrawer: React.FC<HeatmapCellDrawerProps> = ({
  isOpen,
  onClose,
  symbol,
  assetName,
  assetClass,
  category,
  currentPrice,
  modelName,
  horizon,
  metrics,
}) => {
  const router = useRouter();

  if (!isOpen) return null;

  const handleNavigateForecast = () => {
    onClose();
    router.push(`/?symbol=${symbol}`);
  };

  const handleNavigateExplanation = () => {
    onClose();
    router.push(`/?symbol=${symbol}#explanation`);
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#0b1326]/80 backdrop-blur-md flex justify-end p-0 sm:p-4">
      <div className="w-full max-w-md bg-[#171f33] border-l sm:border border-[#2d3449] sm:rounded-2xl shadow-2xl h-full sm:h-auto overflow-y-auto p-6 space-y-6 flex flex-col justify-between">
        <div>
          {/* Header */}
          <div className="flex justify-between items-start pb-4 border-b border-[#2d3449]">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-[#dae2fd]">{symbol}</span>
                <span className="text-xs text-[#818cf8] font-mono font-bold uppercase">× {modelName}</span>
              </div>
              <p className="text-xs text-[#908f9e] font-sans mt-0.5">{assetName}</p>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-[#908f9e] hover:text-[#dae2fd] hover:bg-[#0b1326] transition-all"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Context Details */}
          <div className="py-4 grid grid-cols-2 gap-3 text-xs font-mono border-b border-[#2d3449]">
            <div className="bg-[#0b1326] p-2.5 rounded-xl border border-[#2d3449]">
              <span className="text-[10px] text-[#908f9e] block">ASSET CLASS</span>
              <span className="font-bold text-[#dae2fd] uppercase">{assetClass.replace("_", " ")}</span>
            </div>
            <div className="bg-[#0b1326] p-2.5 rounded-xl border border-[#2d3449]">
              <span className="text-[10px] text-[#908f9e] block">CATEGORY</span>
              <span className="font-bold text-[#dae2fd] truncate block">{category}</span>
            </div>
            <div className="bg-[#0b1326] p-2.5 rounded-xl border border-[#2d3449]">
              <span className="text-[10px] text-[#908f9e] block">CURRENT PRICE</span>
              <span className="font-bold text-[#dae2fd]">{formatCurrency(currentPrice)}</span>
            </div>
            <div className="bg-[#0b1326] p-2.5 rounded-xl border border-[#2d3449]">
              <span className="text-[10px] text-[#908f9e] block">FORECAST HORIZON</span>
              <span className="font-bold text-[#818cf8] uppercase">{horizon}</span>
            </div>
          </div>

          {/* Evaluation Metrics Breakdown */}
          <div className="py-4 space-y-3 font-mono text-xs">
            <h4 className="text-xs font-bold text-[#dae2fd] uppercase tracking-wider flex items-center gap-1.5 font-sans">
              <Target className="h-4 w-4 text-[#818cf8]" /> Quantitative Evaluation Metrics
            </h4>

            {!metrics || !metrics.isAvailable ? (
              <div className="bg-[#0b1326] p-6 rounded-xl border border-[#2d3449] text-center text-[#908f9e]">
                No evaluation data available for {modelName} on {symbol}.
              </div>
            ) : (
              <div className="space-y-2">
                {/* Overall Score Highlight */}
                <div className="bg-[#0b1326] p-3.5 rounded-xl border border-[#4edea3]/30 flex justify-between items-center">
                  <div>
                    <span className="text-[10px] text-[#908f9e] block">OVERALL SCORE</span>
                    <span className="text-xl font-bold text-[#4edea3]">
                      {formatNumber(metrics.overall_score)} / 100.00
                    </span>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-[#4edea3]/10 text-[#4edea3] text-[10px] font-bold">
                    PASSED
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-[#0b1326] p-2.5 rounded-xl border border-[#2d3449]">
                    <span className="text-[10px] text-[#908f9e] block">MAE (Error)</span>
                    <span className="font-bold text-[#dae2fd]">{formatCurrency(metrics.mae)}</span>
                  </div>
                  <div className="bg-[#0b1326] p-2.5 rounded-xl border border-[#2d3449]">
                    <span className="text-[10px] text-[#908f9e] block">RMSE (Error)</span>
                    <span className="font-bold text-[#dae2fd]">{formatCurrency(metrics.rmse)}</span>
                  </div>
                  <div className="bg-[#0b1326] p-2.5 rounded-xl border border-[#2d3449]">
                    <span className="text-[10px] text-[#908f9e] block">MAPE (%)</span>
                    <span className="font-bold text-[#dae2fd]">{formatPercent(metrics.mape_pct)}</span>
                  </div>
                  <div className="bg-[#0b1326] p-2.5 rounded-xl border border-[#2d3449]">
                    <span className="text-[10px] text-[#908f9e] block">R² Variance</span>
                    <span className="font-bold text-[#4edea3]">{formatNumber(metrics.r2_score)}</span>
                  </div>
                </div>

                <div className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449] flex justify-between items-center">
                  <span className="text-[10px] text-[#908f9e]">DIRECTIONAL ACCURACY</span>
                  <span className="font-bold text-[#4edea3]">{formatPercent(metrics.directional_accuracy_pct)}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-4 border-t border-[#2d3449] space-y-2">
          <button
            onClick={handleNavigateForecast}
            className="w-full py-2.5 px-4 bg-[#818cf8] text-[#131e8c] font-bold text-xs rounded-xl shadow hover:bg-[#818cf8]/90 transition-all flex items-center justify-center gap-2"
          >
            <span>View Asset Forecast</span>
            <ArrowUpRight className="h-4 w-4" />
          </button>

          <button
            onClick={handleNavigateExplanation}
            className="w-full py-2.5 px-4 bg-[#0b1326] text-[#dae2fd] font-semibold text-xs rounded-xl border border-[#2d3449] hover:border-[#818cf8]/40 transition-all flex items-center justify-center gap-2"
          >
            <BarChart2 className="h-4 w-4 text-[#818cf8]" />
            <span>View Model Explanation (SHAP)</span>
          </button>
        </div>
      </div>
    </div>
  );
};
