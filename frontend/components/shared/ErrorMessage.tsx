"use client";

import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorMessageProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = "Backend Unreachable",
  message = "Failed to connect to the SarmayaSaaz API server. Please make sure the FastAPI backend is running on port 8000 or 8001.",
  onRetry,
}) => {
  return (
    <div className="bg-[#171f33] border border-[#ffb2b7]/30 rounded-2xl p-8 text-center shadow-2xl max-w-xl mx-auto my-12 space-y-4">
      <div className="h-12 w-12 rounded-2xl bg-[#ffb2b7]/10 border border-[#ffb2b7]/30 flex items-center justify-center mx-auto text-[#ffb2b7]">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <div>
        <h3 className="text-lg font-bold text-[#dae2fd]">{title}</h3>
        <p className="text-xs text-[#c6c5d5] mt-1.5 leading-relaxed">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#818cf8] hover:bg-[#818cf8]/90 text-[#131e8c] font-bold text-xs rounded-xl shadow-lg transition-all active:scale-95 mt-2"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Retry Connection</span>
        </button>
      )}
    </div>
  );
};
