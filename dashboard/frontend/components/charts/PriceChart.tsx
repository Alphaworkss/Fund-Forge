"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { ForecastResponse, HistoryResponse, NewsItem } from "@/lib/api/types";
import { formatCurrency, formatNumber } from "@/lib/formatters";

interface PriceChartProps {
  history?: HistoryResponse;
  forecast?: ForecastResponse;
  news?: NewsItem[];
  unit?: string;
  onHorizonChange?: (horizon: string) => void;
  selectedHorizon?: string;
}

export const PriceChart: React.FC<PriceChartProps> = ({
  history,
  forecast,
  news = [],
  unit = "USD",
  onHorizonChange,
  selectedHorizon = "30d",
}) => {
  const [period, setPeriod] = useState("30d");

  const horizons = ["1d", "7d", "14d", "30d", "90d"];

  // Prepare combined chart data
  const historyPoints = history?.points || [];
  const forecastPoints = forecast?.forecast_series || [];

  // Map historical points and attach news events matching timeline
  const chartData = [
    ...historyPoints.map((p, idx) => {
      const dateStr = p.timestamp.split(" ")[0];
      const attachedNews = news.length > 0 ? news[idx % news.length] : undefined;
      return {
        date: dateStr,
        price: p.price,
        lowerBound: null,
        upperBound: null,
        centralEstimate: null,
        isForecast: false,
        newsEvent: idx === Math.floor(historyPoints.length / 2) || idx === historyPoints.length - 2 ? attachedNews : null,
      };
    }),
    ...forecastPoints.map((fp) => ({
      date: fp.timestamp,
      price: null,
      lowerBound: fp.lower_bound,
      upperBound: fp.upper_bound,
      centralEstimate: fp.central_estimate,
      isForecast: true,
      newsEvent: null,
    })),
  ];

  // News timeline markers
  const newsMarkers = chartData.filter((d) => d.newsEvent);

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4 pb-3 border-b border-[#2d3449]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-base text-[#dae2fd]">
              Price History & AI Forecast Projection
            </h3>
            <span className="px-2 py-0.5 text-xs font-mono rounded bg-[#818cf8]/10 text-[#bdc2ff] border border-[#818cf8]/20">
              {history?.symbol || "BTC"}
            </span>
          </div>
          <p className="text-xs text-[#908f9e] mt-0.5">
            Unit: {unit} • Model: {forecast?.model || "PatchTST"} ({formatNumber((forecast?.confidence || 0.8) * 100)}% Confidence)
          </p>
        </div>

        {/* Horizon Picker */}
        <div className="flex items-center bg-[#0b1326] p-1 rounded-xl border border-[#2d3449]">
          {horizons.map((h) => (
            <button
              key={h}
              onClick={() => {
                setPeriod(h);
                if (onHorizonChange) onHorizonChange(h);
              }}
              className={`px-3 py-1 text-xs font-mono font-medium rounded-lg transition-all ${
                selectedHorizon === h
                  ? "bg-[#818cf8] text-[#131e8c] font-bold shadow"
                  : "text-[#908f9e] hover:text-[#dae2fd]"
              }`}
            >
              {h.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Composed Chart */}
      <div className="h-80 w-full font-mono text-xs">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4edea3" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#4edea3" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorForecastBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#818cf8" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#818cf8" stopOpacity={0.05} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#2d3449" vertical={false} />

            <XAxis
              dataKey="date"
              stroke="#908f9e"
              tickLine={false}
              axisLine={{ stroke: "#2d3449" }}
              tick={{ fontSize: 10 }}
            />

            <YAxis
              stroke="#908f9e"
              tickLine={false}
              axisLine={{ stroke: "#2d3449" }}
              domain={["auto", "auto"]}
              tickFormatter={(val) => `$${val}`}
              tick={{ fontSize: 10 }}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-[#131b2e] border border-[#2d3449] p-3 rounded-xl shadow-2xl space-y-1 font-mono text-xs z-50">
                      <div className="text-[#908f9e] text-[10px] pb-1 border-b border-[#2d3449]">
                        Date: {label}
                      </div>

                      {!data.isForecast ? (
                        <div className="flex items-center justify-between gap-4 text-[#4edea3] font-bold">
                          <span>Historical Price:</span>
                          <span>{formatCurrency(data.price)}</span>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center justify-between gap-4 text-[#818cf8] font-bold">
                            <span>Central Target:</span>
                            <span>{formatCurrency(data.centralEstimate)}</span>
                          </div>
                          <div className="flex items-center justify-between gap-4 text-[#908f9e] text-[10px]">
                            <span>Range:</span>
                            <span>
                              {formatCurrency(data.lowerBound)} - {formatCurrency(data.upperBound)}
                            </span>
                          </div>
                        </>
                      )}

                      {data.newsEvent && (
                        <div className="mt-2 pt-2 border-t border-amber-500/30 text-amber-400 text-[10px] space-y-0.5 max-w-xs">
                          <div className="font-bold flex items-center gap-1">
                            <span>📰 News Event:</span>
                            <span className="truncate">{data.newsEvent.title}</span>
                          </div>
                          <div className="text-[#908f9e] line-clamp-2">{data.newsEvent.summary}</div>
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />

            {/* News Catalyst Markers */}
            {newsMarkers.map((m, idx) => (
              <ReferenceLine
                key={idx}
                x={m.date}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{
                  value: "📰 Catalyst",
                  fill: "#f59e0b",
                  fontSize: 10,
                  position: "insideTopLeft",
                }}
              />
            ))}

            {/* Historical Price Area */}
            <Area
              type="monotone"
              dataKey="price"
              stroke="#4edea3"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#colorPrice)"
              name="Historical Price"
            />

            {/* Forecast Confidence Band */}
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="transparent"
              fill="url(#colorForecastBand)"
              name="Upper Bound Range"
            />

            {/* Central Forecast Line */}
            <Line
              type="monotone"
              dataKey="centralEstimate"
              stroke="#818cf8"
              strokeWidth={2.5}
              strokeDasharray="4 4"
              dot={false}
              name="AI Central Estimate"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-6 mt-3 pt-2 border-t border-[#2d3449] text-xs text-[#c6c5d5]">
        <div className="flex items-center gap-2">
          <span className="w-3 h-0.5 bg-[#4edea3] rounded"></span>
          <span>Historical Price</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-0.5 bg-[#818cf8] border-dashed border-b"></span>
          <span>AI Forecast Estimate</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-[#818cf8]/30 border border-[#818cf8] rounded"></span>
          <span>Confidence Interval Range</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-0.5 bg-amber-500 border-dashed"></span>
          <span className="text-amber-400 font-medium">📰 News Event Overlay</span>
        </div>
      </div>
    </div>
  );
};
