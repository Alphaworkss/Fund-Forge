"use client";

import React from "react";
import { Grid, Cpu, Layers, HelpCircle } from "lucide-react";
import { MetricType, METRIC_DEFINITIONS, HorizonType } from "@/lib/heatmapData";

interface HeatmapHeaderProps {
  viewMode: "asset_class" | "model";
  onViewModeChange: (mode: "asset_class" | "model") => void;
  selectedMetric: MetricType;
  onMetricChange: (metric: MetricType) => void;
  selectedHorizon: HorizonType;
  onHorizonChange: (horizon: HorizonType) => void;
}

export const HeatmapHeader: React.FC<HeatmapHeaderProps> = ({
  viewMode,
  onViewModeChange,
  selectedMetric,
  onMetricChange,
  selectedHorizon,
  onHorizonChange,
}) => {
  const metricDef = METRIC_DEFINITIONS[selectedMetric];

  const horizons: { id: HorizonType; label: string }[] = [
    { id: "1d", label: "1 Day (1D)" },
    { id: "7d", label: "1 Week (7D)" },
    { id: "14d", label: "2 Weeks (14D)" },
    { id: "30d", label: "1 Month (30D)" },
    { id: "90d", label: "3 Months (90D)" },
  ];

  return (
    <div className="space-y-4 bg-[#171f33] p-6 border border-[#2d3449] rounded-2xl shadow-xl">
      {/* Title & Navigation Mode Switcher */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-2 rounded-xl bg-[#818cf8]/10 text-[#818cf8] border border-[#818cf8]/20">
              <Grid className="h-5 w-5" />
            </div>
            <h1 className="text-xl font-bold text-[#dae2fd]">
              Model Performance Heatmap
            </h1>
          </div>
          <p className="text-xs text-[#908f9e]">
            Compare forecasting model performance across asset classes, categories, and individual assets.
          </p>
        </div>

        {/* Primary View Mode Switcher (Mode A vs Mode B) */}
        <div className="flex items-center bg-[#0b1326] p-1 rounded-xl border border-[#2d3449]">
          <button
            onClick={() => onViewModeChange("asset_class")}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
              viewMode === "asset_class"
                ? "bg-[#818cf8] text-[#131e8c] shadow font-bold"
                : "text-[#c6c5d5] hover:text-[#dae2fd]"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Asset Class View</span>
          </button>

          <button
            onClick={() => onViewModeChange("model")}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
              viewMode === "model"
                ? "bg-[#818cf8] text-[#131e8c] shadow font-bold"
                : "text-[#c6c5d5] hover:text-[#dae2fd]"
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>Explore by Model</span>
          </button>
        </div>
      </div>

      {/* Control Ribbon: Metric & Horizon Selectors + Color Legend */}
      <div className="pt-4 border-t border-[#2d3449] flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs">
        <div className="flex flex-wrap items-center gap-4">
          {/* Horizon Selector */}
          <div className="flex items-center gap-2">
            <span className="text-[#908f9e] text-[10px] uppercase tracking-wider">Horizon:</span>
            <div className="flex bg-[#0b1326] p-1 rounded-xl border border-[#2d3449]">
              {horizons.map((h) => (
                <button
                  key={h.id}
                  onClick={() => onHorizonChange(h.id)}
                  className={`px-2.5 py-1 text-[11px] font-bold rounded-lg uppercase transition-all ${
                    selectedHorizon === h.id
                      ? "bg-[#818cf8] text-[#131e8c]"
                      : "text-[#908f9e] hover:text-[#dae2fd]"
                  }`}
                >
                  {h.id}
                </button>
              ))}
            </div>
          </div>

          {/* Metric Selector */}
          <div className="flex items-center gap-2">
            <span className="text-[#908f9e] text-[10px] uppercase tracking-wider">Metric:</span>
            <select
              value={selectedMetric}
              onChange={(e) => onMetricChange(e.target.value as MetricType)}
              className="bg-[#0b1326] text-[#dae2fd] font-bold border border-[#2d3449] rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:border-[#818cf8]"
            >
              {Object.values(METRIC_DEFINITIONS).map((def) => (
                <option key={def.id} value={def.id}>
                  {def.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Dynamic Metric Explanation & Color Scale Legend */}
        <div className="flex items-center gap-4 bg-[#0b1326] px-4 py-2 rounded-xl border border-[#2d3449]">
          <div className="flex items-center gap-1.5 text-[11px]">
            <HelpCircle className="h-3.5 w-3.5 text-[#818cf8]" />
            <span className="text-[#908f9e]">
              {metricDef.higherIsBetter ? (
                <span className="text-[#4edea3] font-bold">Higher value is better</span>
              ) : (
                <span className="text-[#4edea3] font-bold">Lower value is better</span>
              )}
            </span>
          </div>

          {/* Color Scale Bar */}
          <div className="flex items-center gap-2 text-[10px] text-[#908f9e]">
            <span>Worse</span>
            <div className="h-2.5 w-24 rounded-full bg-gradient-to-r from-[#ffb2b7] via-[#818cf8] to-[#4edea3]"></div>
            <span>Better</span>
          </div>
        </div>
      </div>
    </div>
  );
};
