"use client";

import React from "react";
import { NewsItem } from "@/lib/api/types";
import { Newspaper, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { formatNumber } from "@/lib/formatters";

interface DashboardNewsBoxProps {
  news?: NewsItem[];
  symbol: string;
}

export const DashboardNewsBox: React.FC<DashboardNewsBoxProps> = ({ news = [], symbol }) => {
  if (!news || news.length === 0) return null;

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl space-y-4 font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-[#2d3449]">
        <div className="flex items-center gap-2">
          <Newspaper className="h-4 w-4 text-[#818cf8]" />
          <h3 className="font-bold text-sm text-[#dae2fd]">
            {symbol} Market Catalyst Intelligence
          </h3>
        </div>
        <span className="text-[10px] font-mono text-[#818cf8] bg-[#818cf8]/10 px-2 py-0.5 rounded-full border border-[#818cf8]/30">
          LIVE FEED
        </span>
      </div>

      <div className="space-y-3 divide-y divide-[#2d3449]/50">
        {news.slice(0, 3).map((item, idx) => {
          const itemAny = item as any;
          const isPositive = (itemAny.sentiment as string) === "positive" || (itemAny.sentiment as string) === "bullish";
          const isNegative = (itemAny.sentiment as string) === "negative" || (itemAny.sentiment as string) === "bearish";

          return (
            <a
              key={itemAny.id || idx}
              href={itemAny.url || "#"}
              target="_blank"
              rel="noopener noreferrer"
              className="pt-3 first:pt-0 block group hover:bg-[#0b1326]/40 p-2 rounded-xl transition-all"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2 font-mono text-[10px]">
                    <span className="text-[#818cf8] font-bold uppercase">{itemAny.sector || symbol}</span>
                    <span className="text-[#908f9e]">• {itemAny.time || "Recent"}</span>
                  </div>
                  <h4 className="text-xs font-bold text-[#dae2fd] group-hover:text-[#818cf8] transition-colors leading-snug">
                    {itemAny.title}
                  </h4>
                  <p className="text-[11px] text-[#908f9e] line-clamp-2 leading-relaxed">
                    {itemAny.summary}
                  </p>
                </div>

                <div className="flex flex-col items-end gap-1 shrink-0 font-mono">
                  <span
                    className={`flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-full ${
                      isPositive
                        ? "bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30"
                        : isNegative
                        ? "bg-[#ffb2b7]/10 text-[#ffb2b7] border border-[#ffb2b7]/30"
                        : "bg-[#2d3449] text-[#dae2fd]"
                    }`}
                  >
                    {isPositive ? (
                      <TrendingUp className="h-2.5 w-2.5" />
                    ) : isNegative ? (
                      <TrendingDown className="h-2.5 w-2.5" />
                    ) : (
                      <Minus className="h-2.5 w-2.5" />
                    )}
                    {itemAny.sentiment}
                  </span>
                  {itemAny.impactScore !== undefined && (
                    <span className="text-[9px] text-[#908f9e]">
                      Impact: {formatNumber(itemAny.impactScore, 2)}
                    </span>
                  )}
                </div>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
};
