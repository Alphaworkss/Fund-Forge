"use client";

import React from "react";
import { ModelInfoResponse } from "@/lib/api/types";
import { Award, CheckCircle2 } from "lucide-react";
import { formatNumber, formatPercent, formatCurrency } from "@/lib/formatters";

interface Props {
  modelInfo?: ModelInfoResponse;
}

export const ModelMetricsCard: React.FC<Props> = ({ modelInfo }) => {
  if (!modelInfo) return null;

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#2d3449]">
        <div className="flex items-center gap-2">
          <Award className="h-4 w-4 text-[#818cf8]" />
          <h3 className="font-semibold text-base text-[#dae2fd]">
            Model Selection & Accuracy Leaderboard
          </h3>
        </div>
        <span className="text-xs text-[#908f9e] font-mono">
          Winning Model: <span className="text-[#4edea3] font-bold">{modelInfo.selected_model}</span>
        </span>
      </div>

      <div className="space-y-3 font-mono text-xs">
        {modelInfo.candidate_models.map((model) => {
          const isWinner = model.is_winning_model;

          return (
            <div
              key={model.name}
              className={`p-3 rounded-xl border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 ${
                isWinner
                  ? "bg-[#818cf8]/10 border-[#818cf8]/50 shadow-md"
                  : "bg-[#0b1326] border-[#2d3449]"
              }`}
            >
              <div className="flex items-center gap-2">
                {isWinner ? (
                  <CheckCircle2 className="h-4 w-4 text-[#4edea3]" />
                ) : (
                  <div className="h-4 w-4 rounded-full border border-[#908f9e]" />
                )}
                <div>
                  <span className="font-bold text-[#dae2fd] text-sm">{model.name}</span>
                  <span className="text-[10px] text-[#908f9e] block font-sans">
                    {model.architecture}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4 text-right w-full sm:w-auto justify-between sm:justify-end">
                <div>
                  <span className="text-[10px] text-[#908f9e] block">R² SCORE</span>
                  <span className="text-[#dae2fd] font-bold">{formatPercent(model.r2_score * 100)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-[#908f9e] block">MAE</span>
                  <span className="text-[#dae2fd]">{formatCurrency(model.mae)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-[#908f9e] block">MAPE</span>
                  <span className="text-[#4edea3]">{formatPercent(model.mape_pct)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
