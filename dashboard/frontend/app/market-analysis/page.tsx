"use client";

import React, { useState } from "react";
import {
  Brain,
  Calendar,
  Filter,
  RefreshCw,
  Zap,
  ExternalLink,
  CheckCircle2,
} from "lucide-react";
import { formatNumber } from "@/lib/formatters";

interface NewsItem {
  id: string;
  region: string;
  sector: string;
  time: string;
  title: string;
  summary: string;
  sentiment: "positive" | "negative" | "neutral";
  impactScore: number;
  url: string;
}

export default function MarketAnalysisPage() {
  const [selectedRegion, setSelectedRegion] = useState<string>("Global");
  const [activeSectorFilter, setActiveSectorFilter] = useState<string>("all");
  const [isFilterDropdownOpen, setIsFilterDropdownOpen] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [notification, setNotification] = useState<string | null>(null);

  const regionButtons = ["Global", "Local", "PK Markets", "Crypto"];

  const allMajorEvents = [
    {
      id: "evt-1",
      region: "Global",
      title: "Fed Signals Rate Cut Potential",
      time: "Today, 14:00 UTC",
      impact: "High Impact",
      impactColor: "text-[#4edea3] bg-[#4edea3]/10 border-[#4edea3]/30",
      description: "FOMC minutes suggest openness to rate cuts if inflation continues its downward trajectory towards the 2.00% target.",
      tags: [
        { label: "DXY", direction: "down" },
        { label: "SPX", direction: "up" },
        { label: "BTC", direction: "up" },
      ],
    },
    {
      id: "evt-2",
      region: "Global",
      title: "US CPI Inflation Data Release",
      time: "Tomorrow, 12:30 UTC",
      impact: "Critical Data",
      impactColor: "text-[#ffb2b7] bg-[#ffb2b7]/10 border-[#ffb2b7]/30",
      description: "Core CPI expected to show a slight 0.20% uptick month over month. Markets bracing for volatility around release.",
      tags: [
        { label: "Volatility", direction: "up" },
        { label: "US10Y", direction: "neutral" },
      ],
    },
    {
      id: "evt-3",
      region: "PK Markets",
      title: "KSE-100 Benchmark Touches Historical Record High",
      time: "Today, 09:30 PKT",
      impact: "Domestic Record",
      impactColor: "text-[#818cf8] bg-[#818cf8]/10 border-[#818cf8]/20",
      description: "Strong institutional inflows in banking and fertilizer stocks push Karachi Stock Exchange benchmark index past key resistance levels.",
      tags: [
        { label: "KSE-100", direction: "up" },
        { label: "PKR", direction: "stable" },
      ],
    },
    {
      id: "evt-4",
      region: "Local",
      title: "State Bank Monetary Policy Rate Decision",
      time: "Aug 18, 11:00 PKT",
      impact: "Policy Catalyst",
      impactColor: "text-[#4edea3] bg-[#4edea3]/10 border-[#4edea3]/30",
      description: "Analyst consensus anticipates potential rate easing following consecutive monthly declines in headline CPI numbers.",
      tags: [
        { label: "SBP Rate", direction: "down" },
        { label: "Yields", direction: "down" },
      ],
    },
    {
      id: "evt-5",
      region: "Crypto",
      title: "Spot Ethereum Staking Yield Proposals",
      time: "Today, 18:00 UTC",
      impact: "Protocol Upgrade",
      impactColor: "text-[#818cf8] bg-[#818cf8]/10 border-[#818cf8]/30",
      description: "Network consensus upgrades enhance validator efficiency and lower Layer 2 rollup execution costs.",
      tags: [
        { label: "ETH", direction: "up" },
        { label: "L2 Volume", direction: "up" },
      ],
    },
  ];

  // News Items Pool for Dynamic Rotation
  const primaryNewsFeed: NewsItem[] = [
    {
      id: "news-1",
      region: "Global",
      sector: "Technology",
      time: "Just now",
      title: "NVIDIA Announces Accelerated AI Hardware Release Timeline",
      summary: "Unexpected timeline acceleration for next generation architecture sends semiconductor indices surging in early trading.",
      sentiment: "positive",
      impactScore: 92.50,
      url: "https://finance.yahoo.com/quote/NVDA",
    },
    {
      id: "news-2",
      region: "Global",
      sector: "Energy",
      time: "15m ago",
      title: "OPEC Coalition Maintains Extended Output Restrictions",
      summary: "Defying consensus expectations, member states extend supply restrictions through Q3 pushing crude past $85.00 per barrel.",
      sentiment: "negative",
      impactScore: 78.40,
      url: "https://www.bloomberg.com/energy",
    },
    {
      id: "news-3",
      region: "Crypto",
      sector: "Cryptocurrency",
      time: "32m ago",
      title: "Institutional Capital Inflows into Spot Bitcoin Funds Hit Record",
      summary: "Sustained institutional adoption narrative strengthens as net weekly inflows surpass $1.50B across primary custodians.",
      sentiment: "positive",
      impactScore: 88.00,
      url: "https://www.coindesk.com/markets",
    },
    {
      id: "news-4",
      region: "PK Markets",
      sector: "PK Markets",
      time: "1h ago",
      title: "Pakistani Tech Exports Surge by 24.00% Year-over-Year",
      summary: "Official figures confirm strong momentum in IT services export remittances, supporting foreign exchange reserve stability.",
      sentiment: "positive",
      impactScore: 84.10,
      url: "https://www.reuters.com/markets",
    },
    {
      id: "news-5",
      region: "Local",
      sector: "Banking",
      time: "2h ago",
      title: "Local Commercial Banks Post Strong Quarterly Earnings",
      summary: "Robust net interest margins and prudent credit provisioning drive record dividend declarations for shareholders.",
      sentiment: "positive",
      impactScore: 72.80,
      url: "https://finance.yahoo.com",
    },
  ];

  const alternativeNewsPool: NewsItem[] = [
    {
      id: "news-alt-1",
      region: "Global",
      sector: "Technology",
      time: "Just now",
      title: "Microsoft & OpenAI Announce Infrastructure Expansion",
      summary: "Multi-billion dollar hyperscale datacenter expansion targets 50.00% increase in generative AI inference capacity.",
      sentiment: "positive",
      impactScore: 94.80,
      url: "https://finance.yahoo.com/quote/MSFT",
    },
    {
      id: "news-alt-2",
      region: "Crypto",
      sector: "Cryptocurrency",
      time: "Just now",
      title: "Solana Network Throughput Reaches All-Time High",
      summary: "DeFi trading volume and low-latency transaction processing drive active wallet addresses past 2.50M daily users.",
      sentiment: "positive",
      impactScore: 86.40,
      url: "https://www.coindesk.com",
    },
    {
      id: "news-alt-3",
      region: "Global",
      sector: "Commodities",
      time: "Just now",
      title: "Gold Surges Past Target Resistance on Central Bank Buying",
      summary: "Global central banks add 45.00 metric tons of physical gold reserves in sovereign portfolio diversification push.",
      sentiment: "positive",
      impactScore: 89.20,
      url: "https://www.reuters.com/markets/commodities",
    },
    {
      id: "news-alt-4",
      region: "PK Markets",
      sector: "Banking",
      time: "Just now",
      title: "State Bank Foreign Exchange Reserves Increase by $250.00M",
      summary: "Bilateral inflows and remittance growth bolster external account stability, narrowing current account deficits.",
      sentiment: "positive",
      impactScore: 81.50,
      url: "https://www.reuters.com/markets",
    },
  ];

  const [newsFeed, setNewsFeed] = useState<NewsItem[]>(primaryNewsFeed);
  const [reloadToggle, setReloadToggle] = useState<boolean>(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      // Toggle between primary and alternative news pool to guarantee fresh articles
      const freshPool = reloadToggle ? primaryNewsFeed : alternativeNewsPool;
      setReloadToggle(!reloadToggle);
      setNewsFeed(freshPool);

      setNotification("Market Analysis news feed refreshed with latest intelligence!");
      setTimeout(() => setNotification(null), 3500);
    }, 700);
  };

  // Filter events by selected region
  const filteredEvents = allMajorEvents.filter(
    (evt) => selectedRegion === "Global" || evt.region === selectedRegion
  );

  // Filter news by selected region & sector filter
  const filteredNews = newsFeed.filter((news) => {
    const matchesRegion = selectedRegion === "Global" || news.region === selectedRegion;
    const matchesSector = activeSectorFilter === "all" || news.sector.toLowerCase().includes(activeSectorFilter.toLowerCase());
    return matchesRegion && matchesSector;
  });

  return (
    <div className="space-y-6 relative">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 bg-[#818cf8] text-[#131e8c] px-4 py-2.5 rounded-xl font-mono font-bold text-xs shadow-2xl animate-bounce flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          <span>{notification}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#171f33] p-6 border border-[#2d3449] rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <div className="p-2 rounded-xl bg-[#818cf8]/10 text-[#818cf8] border border-[#818cf8]/20">
              <Brain className="h-5 w-5" />
            </div>
            <h1 className="text-xl font-bold text-[#dae2fd]">
              SarmayaSaaz Market Analysis Hub
            </h1>
          </div>
          <p className="text-xs text-[#908f9e]">
            Real-time market sentiment, major financial event catalysts and predictive news impact signals.
          </p>
        </div>

        {/* Region Selector (Global, Local, PK Markets, Crypto) */}
        <div className="flex items-center bg-[#0b1326] p-1 rounded-xl border border-[#2d3449]">
          {regionButtons.map((reg) => (
            <button
              key={reg}
              onClick={() => setSelectedRegion(reg)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                selectedRegion === reg
                  ? "bg-[#818cf8] text-[#131e8c] shadow font-bold"
                  : "text-[#c6c5d5] hover:text-[#dae2fd]"
              }`}
            >
              {reg}
            </button>
          ))}
        </div>
      </div>

      {/* Grid: Global Sentiment & Major Events */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Market Sentiment Card */}
        <div className="lg:col-span-4 bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center pb-3 mb-4 border-b border-[#2d3449]">
              <h3 className="text-xs font-bold text-[#908f9e] uppercase tracking-wider">
                {selectedRegion} Market Sentiment
              </h3>
              <Brain className="h-4 w-4 text-[#4edea3]" />
            </div>

            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-2xl font-bold text-[#4edea3]">Bullish</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30">
                +{formatNumber(15.00)} pts
              </span>
            </div>

            <p className="text-xs text-[#908f9e] leading-relaxed mb-6">
              SarmayaSaaz AI models indicate positive market momentum for {selectedRegion} driven by monetary policy clarity and earnings resilience.
            </p>
          </div>

          {/* Sentiment Gauge representation */}
          <div className="bg-[#0b1326] border border-[#2d3449] rounded-xl p-4 space-y-3">
            <div className="flex justify-between items-center text-[10px] font-mono text-[#908f9e]">
              <span>Extreme Fear</span>
              <span className="text-[#4edea3] font-bold">Neutral</span>
              <span>Extreme Greed</span>
            </div>
            <div className="w-full bg-[#131b2e] h-2.5 rounded-full relative overflow-hidden">
              <div className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-[#ffb2b7] via-[#818cf8] to-[#4edea3] w-[75%]"></div>
            </div>
            <div className="text-right text-[11px] font-mono font-bold text-[#4edea3]">
              Score: {formatNumber(75.00)} / 100.00
            </div>
          </div>
        </div>

        {/* Major Events Calendar */}
        <div className="lg:col-span-8 bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl">
          <div className="flex justify-between items-center pb-3 mb-4 border-b border-[#2d3449]">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-[#818cf8]" />
              <h3 className="text-xs font-bold text-[#908f9e] uppercase tracking-wider">
                Major Market Events & Catalysts ({selectedRegion})
              </h3>
            </div>
            <span className="text-xs text-[#818cf8] font-semibold">Live Calendar</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEvents.map((evt) => (
              <div
                key={evt.id}
                className="bg-[#0b1326] border border-[#2d3449] rounded-xl p-4 hover:border-[#818cf8]/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${evt.impactColor}`}>
                      {evt.impact}
                    </span>
                  </div>
                  <h4 className="font-bold text-xs text-[#dae2fd] mb-1 leading-snug">
                    {evt.title}
                  </h4>
                  <p className="text-[11px] text-[#908f9e] line-clamp-3 mb-3 leading-relaxed">
                    {evt.description}
                  </p>
                </div>

                <div className="pt-2 border-t border-[#2d3449]/50 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-[#908f9e]">
                    {evt.time}
                  </span>
                  <div className="flex gap-1">
                    {evt.tags.map((tg, i) => (
                      <span key={i} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#171f33] text-[#dae2fd] border border-[#2d3449]">
                        {tg.label}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* News Feed & Impact Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* News Feed */}
        <div className="lg:col-span-8 bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-[#2d3449] relative">
            <h3 className="text-xs font-bold text-[#908f9e] uppercase tracking-wider">
              Significant Financial News Feed ({selectedRegion})
            </h3>
            <div className="flex gap-2">
              {/* Functional Sector Filter Button */}
              <div className="relative">
                <button
                  onClick={() => setIsFilterDropdownOpen(!isFilterDropdownOpen)}
                  className="p-1.5 rounded-lg bg-[#0b1326] text-[#908f9e] hover:text-[#dae2fd] border border-[#2d3449] transition-all flex items-center gap-1 text-xs"
                  title="Filter by sector"
                >
                  <Filter className="h-3.5 w-3.5" />
                  <span className="capitalize">{activeSectorFilter}</span>
                </button>

                {isFilterDropdownOpen && (
                  <div className="absolute right-0 top-9 w-40 bg-[#131b2e] border border-[#2d3449] rounded-xl shadow-2xl z-40 py-1 font-sans text-xs divide-y divide-[#2d3449]">
                    {["all", "Technology", "Energy", "Cryptocurrency", "Banking", "Commodities"].map((sec) => (
                      <button
                        key={sec}
                        onClick={() => {
                          setActiveSectorFilter(sec);
                          setIsFilterDropdownOpen(false);
                        }}
                        className="w-full text-left px-3 py-1.5 hover:bg-[#171f33] text-[#dae2fd] capitalize"
                      >
                        {sec}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Functional Refresh Button */}
              <button
                onClick={handleRefresh}
                className={`p-1.5 rounded-lg bg-[#0b1326] text-[#908f9e] hover:text-[#dae2fd] border border-[#2d3449] transition-all ${
                  isRefreshing ? "animate-spin text-[#818cf8]" : ""
                }`}
                title="Refresh news feed"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {filteredNews.map((news) => (
              /* Clickable News Feed Item */
              <a
                key={news.id}
                href={news.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-[#0b1326] p-4 rounded-xl border border-[#2d3449] hover:border-[#818cf8]/60 transition-all group"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2 text-[10px] font-mono">
                      <span className="text-[#818cf8] font-bold uppercase">{news.sector}</span>
                      <span className="text-[#908f9e]">• {news.time}</span>
                      <ExternalLink className="h-3 w-3 text-[#908f9e] opacity-70 group-hover:opacity-100 group-hover:text-[#818cf8]" />
                    </div>
                    <h4 className="font-bold text-sm text-[#dae2fd] group-hover:text-[#818cf8] transition-colors">
                      {news.title}
                    </h4>
                    <p className="text-xs text-[#908f9e] leading-relaxed">{news.summary}</p>
                  </div>

                  <div className="flex sm:flex-col items-end justify-between sm:justify-center gap-1 min-w-[120px]">
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                        news.sentiment === "positive"
                          ? "bg-[#4edea3]/10 text-[#4edea3] border-[#4edea3]/30"
                          : news.sentiment === "negative"
                          ? "bg-[#ffb2b7]/10 text-[#ffb2b7] border-[#ffb2b7]/30"
                          : "bg-[#818cf8]/10 text-[#818cf8] border-[#818cf8]/30"
                      }`}
                    >
                      {news.sentiment}
                    </span>
                    <span className="text-[10px] font-mono text-[#908f9e]">
                      Impact: {formatNumber(news.impactScore)} / 100.00
                    </span>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>

        {/* Sector Heatmap & Drivers */}
        <div className="lg:col-span-4 bg-[#171f33] border border-[#2d3449] rounded-2xl p-5 shadow-xl space-y-4">
          <div className="pb-3 border-b border-[#2d3449]">
            <h3 className="text-xs font-bold text-[#908f9e] uppercase tracking-wider">
              Asset Class Sentiment Breakdown
            </h3>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {[
              { class: "Cryptocurrencies", score: 82.40, status: "+3.20%", color: "text-[#4edea3]" },
              { class: "Technology Stocks", score: 76.10, status: "+1.80%", color: "text-[#4edea3]" },
              { class: "Precious Metals", score: 68.90, status: "+0.50%", color: "text-[#4edea3]" },
              { class: "PK KSE-100 Index", score: 84.10, status: "+2.10%", color: "text-[#4edea3]" },
              { class: "Energy & Oil", score: 42.10, status: "-1.40%", color: "text-[#ffb2b7]" },
            ].map((item, idx) => (
              <div key={idx} className="bg-[#0b1326] p-3 rounded-xl border border-[#2d3449] flex items-center justify-between">
                <div>
                  <div className="font-bold text-[#dae2fd]">{item.class}</div>
                  <div className="text-[10px] text-[#908f9e]">Sentiment Index: {formatNumber(item.score)}</div>
                </div>
                <span className={`font-bold ${item.color}`}>{item.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
