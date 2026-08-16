"use client";

import React from "react";
import { Cpu, Award, Layers, ShieldCheck, Database, Network } from "lucide-react";

export default function MethodologyPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-[#171f33] p-6 border border-[#2d3449] rounded-2xl shadow-xl space-y-2">
        <div className="flex items-center gap-2 text-[#818cf8]">
          <Cpu className="h-5 w-5" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider">ARCHITECTURE & AI SCIENCE</span>
        </div>
        <h1 className="text-2xl font-bold text-[#dae2fd]">
          SarmayaSaaz AI Forecasting Engine Methodology
        </h1>
        <p className="text-xs text-[#c6c5d5] leading-relaxed">
          Deep-dive explanation of our multi-model time series forecasting algorithms, SHAP explainability matrices, walk-forward evaluation protocol and multi-asset provider abstraction.
        </p>
      </div>

      {/* Model Architectures Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl space-y-2">
          <div className="flex items-center gap-2 text-[#4edea3]">
            <Award className="h-4 w-4" />
            <h3 className="font-bold text-sm text-[#dae2fd]">PatchTST (Patch Time Series Transformer)</h3>
          </div>
          <p className="text-xs text-[#908f9e] leading-relaxed">
            Segments sub-sampled time series into sub-vector patches, retaining local semantic relationships while reducing attention matrix complexity. Winning model for high-frequency cryptocurrency volatility forecasting.
          </p>
        </div>

        <div className="bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl space-y-2">
          <div className="flex items-center gap-2 text-[#818cf8]">
            <Layers className="h-4 w-4" />
            <h3 className="font-bold text-sm text-[#dae2fd]">Temporal Fusion Transformer (TFT)</h3>
          </div>
          <p className="text-xs text-[#908f9e] leading-relaxed">
            Combines multi-horizon forecasting with variable selection networks and static covariate encoders to learn interpretable temporal dynamics across multi-asset universes.
          </p>
        </div>

        <div className="bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl space-y-2">
          <div className="flex items-center gap-2 text-[#818cf8]">
            <Database className="h-4 w-4" />
            <h3 className="font-bold text-sm text-[#dae2fd]">LightGBM & XGBoost Ensembles</h3>
          </div>
          <p className="text-xs text-[#908f9e] leading-relaxed">
            Gradient boosted decision tree architectures trained with lag features, rolling statistics, technical indicators (RSI, MACD, Bollinger Bands) and fundamental valuation multiples. Winning models for equities and commodities.
          </p>
        </div>

        <div className="bg-[#171f33] p-5 border border-[#2d3449] rounded-2xl space-y-2">
          <div className="flex items-center gap-2 text-[#908f9e]">
            <Network className="h-4 w-4" />
            <h3 className="font-bold text-sm text-[#dae2fd]">ARIMA & Statistical Baseline</h3>
          </div>
          <p className="text-xs text-[#908f9e] leading-relaxed">
            AutoRegressive Integrated Moving Average baseline used during walk-forward cross validation to benchmark machine learning improvement ratios.
          </p>
        </div>
      </div>

      {/* SHAP & Validation Protocol */}
      <div className="bg-[#171f33] p-6 border border-[#2d3449] rounded-2xl shadow-xl space-y-4 font-mono text-xs">
        <h3 className="font-bold text-sm text-[#dae2fd] font-sans flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-[#4edea3]" />
          SHAP Explainability & Walk-Forward Protocol
        </h3>
        <p className="text-[#c6c5d5] leading-relaxed font-sans">
          To maintain transparency and prevent cognitive overload, every price target prediction is accompanied by SHAP (SHapley Additive exPlanations) values. Feature contributions quantify the exact impact of macro indicators, earnings surprises, on-chain metrics and technical momentum.
        </p>

        <div className="bg-[#0b1326] p-4 rounded-xl border border-[#2d3449] space-y-2">
          <div className="text-[#818cf8] font-bold">CROSS VALIDATION PROTOCOL</div>
          <div className="text-[#908f9e]">
            • Method: Walk-Forward Expanding Window Validation (no future lookahead bias)<br />
            • Scaling: RobustScaler (resilient to crypto and commodity price spikes)<br />
            • Evaluation Metrics: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE) and R² Score
          </div>
        </div>
      </div>
    </div>
  );
}
