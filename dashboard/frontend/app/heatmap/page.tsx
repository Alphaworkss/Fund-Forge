"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  getMasterHeatmapData,
  getOverallAssetClassSummaryRows,
  AssetClassGroup,
  MetricType,
  HorizonType,
  ModelName,
  AssetHeatmapEntry,
  CellMetrics,
  METRIC_DEFINITIONS,
} from "@/lib/heatmapData";
import { HeatmapHeader } from "@/components/heatmap/HeatmapHeader";
import { HeatmapSummaryCards } from "@/components/heatmap/HeatmapSummaryCards";
import { HeatmapTable } from "@/components/heatmap/HeatmapTable";
import { HeatmapCellDrawer } from "@/components/heatmap/HeatmapCellDrawer";
import { ModelViewExplorer } from "@/components/heatmap/ModelViewExplorer";
import { Skeleton } from "@/components/ui/Skeleton";
import { Search, ChevronRight, ArrowUpDown, Globe } from "lucide-react";

function HeatmapContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Master State Management
  const [data, setData] = useState<AssetClassGroup[]>([]);
  const [loading, setLoading] = useState(true);

  const [viewMode, setViewMode] = useState<"asset_class" | "model">(
    (searchParams.get("mode") as "asset_class" | "model") || "asset_class"
  );
  const [selectedAssetClass, setSelectedAssetClass] = useState<string>(
    searchParams.get("assetClass") || "overall"
  );
  const [selectedCategory, setSelectedCategory] = useState<string | null>(
    searchParams.get("category") || null
  );
  const [selectedMetric, setSelectedMetric] = useState<MetricType>(
    (searchParams.get("metric") as MetricType) || "overall_score"
  );
  const [selectedHorizon, setSelectedHorizon] = useState<HorizonType>(
    (searchParams.get("horizon") as HorizonType) || "30d"
  );
  const [searchQuery, setSearchQuery] = useState<string>(
    searchParams.get("search") || ""
  );
  const [sortMode, setSortMode] = useState<"best" | "worst" | "alphabetical">(
    "best"
  );

  // Cell Drawer State
  const [activeDrawerCell, setActiveDrawerCell] = useState<{
    asset: AssetHeatmapEntry;
    model: ModelName;
    metrics: CellMetrics | null;
  } | null>(null);

  // Load dataset
  useEffect(() => {
    const rawData = getMasterHeatmapData();
    setData(rawData);
    setLoading(false);
  }, []);

  // Update URL SearchParams cleanly
  useEffect(() => {
    const params = new URLSearchParams();
    params.set("mode", viewMode);
    params.set("assetClass", selectedAssetClass);
    if (selectedCategory) params.set("category", selectedCategory);
    params.set("metric", selectedMetric);
    params.set("horizon", selectedHorizon);
    if (searchQuery) params.set("search", searchQuery);

    router.replace(`/heatmap?${params.toString()}`, { scroll: false });
  }, [viewMode, selectedAssetClass, selectedCategory, selectedMetric, selectedHorizon, searchQuery, router]);

  // Overall Asset Class Summary Rows (Cryptocurrencies, Stocks, Mutual Funds, Commodities)
  const overallClassSummaryRows = useMemo(() => {
    if (data.length === 0) return [];
    return getOverallAssetClassSummaryRows(data);
  }, [data]);

  // Current active Asset Class Group
  const activeClassGroup = useMemo(() => {
    return data.find((ac) => ac.id === selectedAssetClass) || null;
  }, [data, selectedAssetClass]);

  // All assets flattened under active selection (with unified search & sorting support)
  const currentAssets = useMemo(() => {
    let list: AssetHeatmapEntry[] = [];

    if (selectedAssetClass === "overall") {
      list = overallClassSummaryRows;
    } else if (activeClassGroup) {
      if (selectedCategory) {
        const cat = activeClassGroup.categories.find((c) => c.name === selectedCategory);
        list = cat ? cat.assets : [];
      } else {
        activeClassGroup.categories.forEach((cat) => {
          list = list.concat(cat.assets);
        });
      }
    }

    // Apply Search Filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (a) =>
          a.symbol.toLowerCase().includes(q) ||
          a.name.toLowerCase().includes(q) ||
          a.category.toLowerCase().includes(q)
      );
    }

    // Apply Sorting (Works for both Overall Market view and individual Asset Class views)
    const higherIsBetter = METRIC_DEFINITIONS[selectedMetric].higherIsBetter;

    return [...list].sort((a, b) => {
      if (sortMode === "alphabetical") {
        return a.name.localeCompare(b.name);
      }

      // Sort by score using TFT model as reference for row order
      const scoreA = a.models["TFT"]?.[selectedHorizon]?.[selectedMetric] ?? 0;
      const scoreB = b.models["TFT"]?.[selectedHorizon]?.[selectedMetric] ?? 0;

      if (sortMode === "best") {
        return higherIsBetter ? scoreB - scoreA : scoreA - scoreB;
      } else {
        return higherIsBetter ? scoreA - scoreB : scoreB - scoreA;
      }
    });
  }, [selectedAssetClass, overallClassSummaryRows, activeClassGroup, selectedCategory, searchQuery, sortMode, selectedMetric, selectedHorizon]);

  // Calculate Summary Cards Data
  const summaryData = useMemo(() => {
    let totalCount = 0;
    let topScore = 0;
    let topSymbol = "BTC";

    data.forEach((ac) => {
      ac.categories.forEach((cat) => {
        cat.assets.forEach((ast) => {
          totalCount++;
          const score = ast.models["PatchTST"]["30d"]?.overall_score || 0;
          if (score > topScore) {
            topScore = score;
            topSymbol = ast.symbol;
          }
        });
      });
    });

    return {
      bestModel: "PatchTST",
      bestAssetClass: "Cryptocurrencies",
      bestAsset: topSymbol,
      bestAssetScore: topScore || 94.20,
      totalAssetsCount: totalCount || 38,
    };
  }, [data]);

  const handleSelectHeatmapCell = (
    asset: AssetHeatmapEntry,
    model: ModelName,
    metrics: CellMetrics | null
  ) => {
    // If in Overall Market view, clicking an overall asset class row drills down into that class
    if (selectedAssetClass === "overall") {
      const targetId = asset.assetClass;
      setSelectedAssetClass(targetId);
      setSelectedCategory(null);
      return;
    }
    setActiveDrawerCell({ asset, model, metrics });
  };

  if (loading) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="space-y-6">
      {/* Master Header with Mode Switcher & Metric Controls */}
      <HeatmapHeader
        viewMode={viewMode}
        onViewModeChange={(m) => setViewMode(m)}
        selectedMetric={selectedMetric}
        onMetricChange={(m) => setSelectedMetric(m)}
        selectedHorizon={selectedHorizon}
        onHorizonChange={(h) => setSelectedHorizon(h)}
      />

      {/* Top Bento Summary Cards */}
      <HeatmapSummaryCards
        bestModel={summaryData.bestModel}
        bestAssetClass={summaryData.bestAssetClass}
        bestAsset={summaryData.bestAsset}
        bestAssetScore={summaryData.bestAssetScore}
        totalAssetsCount={summaryData.totalAssetsCount}
      />

      {/* Mode A — Asset Class View Mode */}
      {viewMode === "asset_class" ? (
        <div className="space-y-6">
          {/* Asset Class Selector Tabs (Includes Overall Market Tab) */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#171f33] p-4 border border-[#2d3449] rounded-2xl shadow-xl">
            {/* Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-1 sm:pb-0">
              <button
                onClick={() => {
                  setSelectedAssetClass("overall");
                  setSelectedCategory(null);
                }}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 ${
                  selectedAssetClass === "overall"
                    ? "bg-[#818cf8] text-[#131e8c] shadow font-bold"
                    : "bg-[#0b1326] text-[#c6c5d5] hover:bg-[#131b2e] border border-[#2d3449]"
                }`}
              >
                <Globe className="h-3.5 w-3.5" />
                <span>Overall Market</span>
              </button>

              {data.map((ac) => (
                <button
                  key={ac.id}
                  onClick={() => {
                    setSelectedAssetClass(ac.id);
                    setSelectedCategory(null);
                  }}
                  className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
                    selectedAssetClass === ac.id
                      ? "bg-[#818cf8] text-[#131e8c] shadow font-bold"
                      : "bg-[#0b1326] text-[#c6c5d5] hover:bg-[#131b2e] border border-[#2d3449]"
                  }`}
                >
                  {ac.name}
                </button>
              ))}
            </div>

            {/* Search & Sort Controls */}
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-56">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search symbol, category, model..."
                  className="w-full bg-[#0b1326] text-[#dae2fd] placeholder-[#908f9e] text-xs rounded-xl pl-9 pr-3 py-2 border border-[#2d3449] focus:outline-none focus:border-[#818cf8]"
                />
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#908f9e]" />
              </div>

              {/* Sort Mode Dropdown */}
              <div className="flex items-center gap-1 bg-[#0b1326] px-3 py-2 rounded-xl border border-[#2d3449] text-xs font-mono">
                <ArrowUpDown className="h-3.5 w-3.5 text-[#818cf8]" />
                <select
                  value={sortMode}
                  onChange={(e) => setSortMode(e.target.value as any)}
                  className="bg-transparent text-[#dae2fd] focus:outline-none text-xs font-bold"
                >
                  <option value="best" className="bg-[#0b1326]">Best Performance</option>
                  <option value="worst" className="bg-[#0b1326]">Worst Performance</option>
                  <option value="alphabetical" className="bg-[#0b1326]">Alphabetical</option>
                </select>
              </div>
            </div>
          </div>

          {/* Interactive Breadcrumbs */}
          <div className="flex items-center gap-2 font-mono text-xs text-[#908f9e]">
            <button
              onClick={() => {
                setSelectedAssetClass("overall");
                setSelectedCategory(null);
              }}
              className="hover:text-[#818cf8] transition-colors"
            >
              Heatmap
            </button>
            <ChevronRight className="h-3.5 w-3.5" />
            <button
              onClick={() => setSelectedCategory(null)}
              className={`hover:text-[#818cf8] transition-colors ${
                !selectedCategory ? "text-[#dae2fd] font-bold" : ""
              }`}
            >
              {selectedAssetClass === "overall" ? "Overall Market Overview" : activeClassGroup?.name}
            </button>

            {selectedCategory && (
              <>
                <ChevronRight className="h-3.5 w-3.5" />
                <span className="text-[#dae2fd] font-bold">{selectedCategory}</span>
              </>
            )}
          </div>

          {/* Overall Market View Banner Notice */}
          {selectedAssetClass === "overall" && (
            <div className="bg-[#171f33] p-4 border border-[#818cf8]/30 rounded-2xl flex items-center justify-between font-mono text-xs">
              <div className="flex items-center gap-2 text-[#dae2fd]">
                <Globe className="h-4 w-4 text-[#818cf8]" />
                <span>
                  Showing <strong>All Asset Classes Overall Heatmap</strong> (Median aggregated performance across models).
                </span>
              </div>
              <span className="text-[#818cf8] text-[10px] uppercase font-bold">
                Click any row to drill down
              </span>
            </div>
          )}

          {/* Category Overview Cards when no category is filtered */}
          {selectedAssetClass !== "overall" && !selectedCategory && activeClassGroup && (
            <div className="bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl space-y-4">
              <div className="pb-3 border-b border-[#2d3449]">
                <h3 className="text-xs font-bold text-[#dae2fd] uppercase tracking-wider">
                  {activeClassGroup.name} Categories Overview ({activeClassGroup.categories.length} Categories)
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {activeClassGroup.categories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.name)}
                    className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449] hover:border-[#818cf8]/60 transition-all text-left group"
                  >
                    <div className="font-bold text-xs text-[#dae2fd] group-hover:text-[#818cf8] transition-colors truncate">
                      {cat.name}
                    </div>
                    <div className="text-[10px] text-[#908f9e] font-mono mt-1">
                      {cat.assets.length} Assets
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Main 2D Heatmap Matrix Table */}
          {currentAssets.length === 0 ? (
            <div className="bg-[#171f33] p-12 rounded-2xl border border-[#2d3449] text-center text-[#908f9e] font-mono text-xs">
              No assets or models found matching search query "{searchQuery}".
            </div>
          ) : (
            <HeatmapTable
              assets={currentAssets}
              selectedMetric={selectedMetric}
              selectedHorizon={selectedHorizon}
              onSelectCell={handleSelectHeatmapCell}
            />
          )}
        </div>
      ) : (
        /* Mode B — Explore by Model Mode */
        <ModelViewExplorer
          data={data}
          selectedMetric={selectedMetric}
          selectedHorizon={selectedHorizon}
          onSelectCell={handleSelectHeatmapCell}
        />
      )}

      {/* Interactive Cell Detail Slide-Over Drawer */}
      {activeDrawerCell && (
        <HeatmapCellDrawer
          isOpen={!!activeDrawerCell}
          onClose={() => setActiveDrawerCell(null)}
          symbol={activeDrawerCell.asset.symbol}
          assetName={activeDrawerCell.asset.name}
          assetClass={activeDrawerCell.asset.assetClass}
          category={activeDrawerCell.asset.category}
          currentPrice={activeDrawerCell.asset.currentPrice}
          modelName={activeDrawerCell.model}
          horizon={selectedHorizon}
          metrics={activeDrawerCell.metrics}
        />
      )}
    </div>
  );
}

export default function HeatmapPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <HeatmapContent />
    </Suspense>
  );
}
