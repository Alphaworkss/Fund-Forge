"use client";

import React from "react";
import { FeatureImportanceResponse } from "@/lib/api/types";
import { Cpu } from "lucide-react";
import { formatNumber } from "@/lib/formatters";

interface FeatureImportanceChartProps {
  features?: FeatureImportanceResponse;
}

export const FeatureImportanceChart: React.FC<FeatureImportanceChartProps> = ({
  features,
}) => {
  const factors = features?.factors || [];

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#2d3449]">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-[#818cf8]" />
          <h3 className="font-semibold text-base text-[#dae2fd]">
            AI Forecast Drivers & Explainability (SHAP)
          </h3>
        </div>
        <span className="text-xs text-[#908f9e] font-mono">
          {features?.symbol} • {features?.asset_type.toUpperCase()}
        </span>
      </div>

      <p className="text-xs text-[#c6c5d5] mb-4 bg-[#0b1326] p-2.5 rounded-lg border border-[#2d3449]">
        {features?.summary || "Factors influencing price forecast."}
      </p>

      {/* Factor Bars */}
      <div className="space-y-3">
        {factors.map((factor, idx) => {
          const isBullish = factor.shap_value >= 0;
          const absVal = Math.min(Math.abs(factor.shap_value) * 200, 100);

          return (
            <div key={idx} className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-[#dae2fd]">
                  {factor.name}
                </span>
                <span
                  className={`font-mono text-xs font-semibold ${
                    isBullish ? "text-[#4edea3]" : "text-[#ffb2b7]"
                  }`}
                >
                  {isBullish ? "+" : ""}
                  {formatNumber(factor.shap_value)} SHAP
                </span>
              </div>
              <p className="text-[11px] text-[#908f9e]">
                {factor.description}
              </p>
              <div className="h-2 w-full bg-[#0b1326] rounded-full overflow-hidden flex">
                <div
                  style={{ width: `${absVal}%` }}
                  className={`h-full rounded-full transition-all duration-500 ${
                    isBullish ? "bg-[#4edea3]" : "bg-[#ffb2b7]"
                  }`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
