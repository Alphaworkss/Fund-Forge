"use client";

import React from "react";
import { TradeTransaction } from "@/lib/api/types";
import { History } from "lucide-react";

interface Props {
  transactions: TradeTransaction[];
}

export const TransactionHistory: React.FC<Props> = ({ transactions }) => {
  if (transactions.length === 0) return null;

  return (
    <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#2d3449]">
        <History className="h-4 w-4 text-[#818cf8]" />
        <h3 className="font-semibold text-base text-[#dae2fd]">Trade Execution Log</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse font-mono text-xs">
          <thead>
            <tr className="border-b border-[#2d3449] text-[#908f9e] text-[10px]">
              <th className="py-2 px-3">TIMESTAMP</th>
              <th className="py-2 px-3">SYMBOL</th>
              <th className="py-2 px-3">TYPE</th>
              <th className="py-2 px-3 text-right">QUANTITY</th>
              <th className="py-2 px-3 text-right">EXECUTION PRICE</th>
              <th className="py-2 px-3 text-right">TOTAL COST</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#2d3449]">
            {transactions.map((tx) => (
              <tr key={tx.id} className="hover:bg-[#131b2e]/50 text-xs">
                <td className="py-2.5 px-3 text-[#908f9e]">{tx.timestamp}</td>
                <td className="py-2.5 px-3 font-bold text-[#dae2fd]">{tx.symbol}</td>
                <td className="py-2.5 px-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      tx.action === "BUY"
                        ? "bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30"
                        : "bg-[#ffb2b7]/10 text-[#ffb2b7] border border-[#ffb2b7]/30"
                    }`}
                  >
                    {tx.action}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-right text-[#dae2fd]">
                  {tx.quantity.toLocaleString()}
                </td>
                <td className="py-2.5 px-3 text-right text-[#c6c5d5]">
                  ${tx.execution_price.toLocaleString()}
                </td>
                <td className="py-2.5 px-3 text-right font-bold text-[#818cf8]">
                  ${tx.total_cost.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
