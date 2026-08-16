"use client";

import React from "react";
import { PositionHolding } from "@/lib/api/types";
import { Briefcase, TrendingUp, TrendingDown } from "lucide-react";

interface Props {
  holdings: PositionHolding[];
  onSellClick?: (holding: PositionHolding) => void;
}

export const HoldingsTable: React.FC<Props> = ({ holdings, onSellClick }) => {
  if (holdings.length === 0) {
    return (
      <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-8 text-center text-[#908f9e]">
        <Briefcase className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-xs">No open positions in portfolio. Use Trade Simulator to buy assets.</p>
      </div>
    );
  }

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#2d3449]">
        <div className="flex items-center gap-2">
          <Briefcase className="h-4 w-4 text-[#818cf8]" />
          <h3 className="font-semibold text-base text-[#dae2fd]">
            Current Portfolio Holdings ({holdings.length})
          </h3>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse font-mono text-xs">
          <thead>
            <tr className="border-b border-[#2d3449] text-[#908f9e] text-[10px]">
              <th className="py-2.5 px-3">ASSET</th>
              <th className="py-2.5 px-3 text-right">HOLDINGS</th>
              <th className="py-2.5 px-3 text-right">AVG BUY PRICE</th>
              <th className="py-2.5 px-3 text-right">CURRENT PRICE</th>
              <th className="py-2.5 px-3 text-right">MARKET VALUE</th>
              <th className="py-2.5 px-3 text-right">UNREALIZED P&L</th>
              <th className="py-2.5 px-3 text-center">ACTION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#2d3449]">
            {holdings.map((h) => {
              const isPositive = h.unrealized_pnl >= 0;

              return (
                <tr key={h.symbol} className="hover:bg-[#131b2e]/50 transition-colors">
                  <td className="py-3 px-3">
                    <div className="flex flex-col">
                      <span className="font-bold text-[#dae2fd] text-sm">{h.name}</span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-[#818cf8]">{h.symbol}</span>
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#0b1326] text-[#908f9e] uppercase border border-[#2d3449]">
                          {h.asset_type.replace("_", " ")}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-right font-bold text-[#dae2fd]">
                    {h.quantity.toLocaleString()}
                  </td>
                  <td className="py-3 px-3 text-right text-[#c6c5d5]">
                    ${h.avg_buy_price.toLocaleString()}
                  </td>
                  <td className="py-3 px-3 text-right text-[#dae2fd]">
                    ${h.current_price.toLocaleString()}
                  </td>
                  <td className="py-3 px-3 text-right font-bold text-[#dae2fd]">
                    ${h.current_market_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <div className={`flex flex-col items-end font-bold ${isPositive ? "text-[#4edea3]" : "text-[#ffb2b7]"}`}>
                      <span>
                        {isPositive ? "+" : ""}${h.unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                      <span className="text-[10px]">
                        ({isPositive ? "+" : ""}{h.unrealized_pnl_pct.toFixed(2)}%)
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-center">
                    {onSellClick && (
                      <button
                        onClick={() => onSellClick(h)}
                        className="px-2.5 py-1 bg-[#ffb2b7]/10 hover:bg-[#ffb2b7]/20 border border-[#ffb2b7]/30 text-[#ffb2b7] text-[11px] rounded-lg font-bold transition-all"
                      >
                        SELL
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
