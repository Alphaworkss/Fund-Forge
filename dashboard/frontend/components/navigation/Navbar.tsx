"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Search,
  Cpu,
  Award,
  Sun,
  Moon,
  Brain,
  Bookmark,
  LayoutDashboard,
  LineChart,
  Store,
  BookOpen,
  Grid,
  ChevronDown,
  MoreHorizontal,
  Briefcase,
} from "lucide-react";
import { ApiService } from "@/lib/api/services";
import { BaseAsset } from "@/lib/api/types";
import { formatCurrency, formatPercent } from "@/lib/formatters";
import { useHiddenFeatures } from "@/lib/featureFlags";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const hiddenFeaturesEnabled = useHiddenFeatures();

  const [searchQuery, setSearchQuery] = useState("");
  const [assets, setAssets] = useState<BaseAsset[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  const searchRef = useRef<HTMLDivElement>(null);
  const moreMenuRef = useRef<HTMLDivElement>(null);

  // Primary Quick-Access Nav Links
  const primaryNavLinks = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Top Movers", href: "/top-movers", icon: Award },
    { name: "Markets", href: "/market", icon: Store },
    { name: "Forecast", href: "/forecasts", icon: LineChart },
    { name: "Watchlist", href: "/watchlist", icon: Bookmark },
    { name: "Model Heatmap", href: "/heatmap", icon: Grid },
  ];

  // Secondary Tools (Grouped cleanly inside "More / Intelligence" Dropdown)
  // Paper Trading ONLY appears if hiddenFeaturesEnabled is TRUE!
  const secondaryNavLinks = [
    ...(hiddenFeaturesEnabled
      ? [{ name: "Paper Trading", href: "/paper-trading", icon: Briefcase, desc: "Virtual Capital Simulator" }]
      : []),
    { name: "Market Analysis", href: "/market-analysis", icon: Brain, desc: "Global Sentiment & Catalysts" },
    { name: "Methodology", href: "/methodology", icon: BookOpen, desc: "AI Models & Architecture" },
  ];

  // Theme setup and toggle
  useEffect(() => {
    const savedTheme = (localStorage.getItem("theme") as "dark" | "light") || "dark";
    setTheme(savedTheme);
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  useEffect(() => {
    ApiService.getAssets()
      .then((res) => setAssets(res.assets))
      .catch((err) => console.error("Failed to load assets for search", err));
  }, []);

  // Close search and dropdown menus on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
      if (moreMenuRef.current && !moreMenuRef.current.contains(e.target as Node)) {
        setIsMoreMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const matchingAssets = searchQuery.trim()
    ? assets.filter(
        (a) =>
          a.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
          a.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  const handleSelectAsset = (symbol: string) => {
    setSearchQuery("");
    setIsOpen(false);
    router.push(`/?symbol=${symbol}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && matchingAssets.length > 0) {
      handleSelectAsset(matchingAssets[0].symbol);
    }
  };

  const isSecondaryActive = secondaryNavLinks.some((l) => l.href === pathname);

  return (
    <header className="fixed top-0 left-0 w-full z-50 bg-[#0b1326]/80 backdrop-blur-xl border-b border-[#2d3449]">
      {/* Symmetrical Container matching <main> (max-w-[1440px] px-4 sm:px-6) */}
      <div className="max-w-[1440px] w-full mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-[#818cf8] to-[#4edea3] flex items-center justify-center text-[#0b1326] font-bold text-lg shadow-lg shadow-[#818cf8]/20">
            <Cpu className="h-5 w-5 stroke-[2.5]" />
          </div>
          <Link href="/" className="flex flex-col">
            <span className="font-bold text-xl text-[#dae2fd] tracking-tight font-sans">
              SarmayaSaaz
            </span>
          </Link>

          {/* Demo Mode Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#818cf8]/10 border border-[#818cf8]/30 text-[#818cf8] text-xs font-mono font-medium ml-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#4edea3] animate-pulse"></span>
            DEMO MODE
          </div>
        </div>

        {/* Streamlined Navigation Links */}
        <nav className="hidden lg:flex items-center gap-5">
          {primaryNavLinks.map((link) => {
            const isActive = pathname === link.href;
            const IconComp = link.icon;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`text-xs font-semibold transition-colors duration-200 py-1 border-b-2 flex items-center gap-1.5 ${
                  isActive
                    ? "text-[#818cf8] font-bold border-[#818cf8]"
                    : "text-[#c6c5d5] border-transparent hover:text-[#818cf8]"
                }`}
              >
                <IconComp className="h-3.5 w-3.5" />
                <span>{link.name}</span>
              </Link>
            );
          })}

          {/* Sleek Dropdown for Secondary Pages */}
          <div className="relative" ref={moreMenuRef}>
            <button
              onClick={() => setIsMoreMenuOpen(!isMoreMenuOpen)}
              className={`text-xs font-semibold transition-colors duration-200 py-1 border-b-2 flex items-center gap-1 ${
                isSecondaryActive
                  ? "text-[#818cf8] font-bold border-[#818cf8]"
                  : "text-[#c6c5d5] border-transparent hover:text-[#818cf8]"
              }`}
            >
              <MoreHorizontal className="h-4 w-4" />
              <span>More</span>
              <ChevronDown className="h-3 w-3 opacity-70" />
            </button>

            {isMoreMenuOpen && (
              <div className="absolute right-0 top-10 w-60 bg-[#131b2e] border border-[#2d3449] rounded-2xl shadow-2xl overflow-hidden z-50 p-1.5 space-y-1 font-sans text-xs divide-y divide-[#2d3449]/50">
                {secondaryNavLinks.map((sLink) => {
                  const IconComp = sLink.icon;
                  const isActive = pathname === sLink.href;
                  return (
                    <Link
                      key={sLink.name}
                      href={sLink.href}
                      onClick={() => setIsMoreMenuOpen(false)}
                      className={`flex items-start gap-2.5 p-2.5 rounded-xl transition-all ${
                        isActive
                          ? "bg-[#818cf8]/10 text-[#818cf8] font-bold"
                          : "text-[#dae2fd] hover:bg-[#171f33]"
                      }`}
                    >
                      <IconComp className="h-4 w-4 text-[#818cf8] shrink-0 mt-0.5" />
                      <div>
                        <div className="font-bold">{sLink.name}</div>
                        <div className="text-[10px] text-[#908f9e] font-mono">{sLink.desc}</div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </nav>

        {/* Right Controls & Interactive Search Bar */}
        <div className="flex items-center gap-3">
          <div className="relative hidden md:block" ref={searchRef}>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsOpen(true);
                }}
                onFocus={() => setIsOpen(true)}
                onKeyDown={handleKeyDown}
                placeholder="Search BTC, AAPL, Gold..."
                className="w-52 bg-[#131b2e] text-[#dae2fd] placeholder-[#908f9e] text-xs rounded-xl pl-8 pr-3 py-1.5 border border-[#2d3449] focus:outline-none focus:border-[#818cf8] transition-colors"
              />
              <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-[#908f9e]" />
            </div>

            {/* Dynamic Search Dropdown Results */}
            {isOpen && searchQuery.trim() !== "" && (
              <div className="absolute right-0 top-10 w-80 bg-[#131b2e] border border-[#2d3449] rounded-2xl shadow-2xl overflow-hidden z-50 font-mono text-xs max-h-80 overflow-y-auto divide-y divide-[#2d3449]">
                {matchingAssets.length === 0 ? (
                  <div className="p-4 text-center text-[#908f9e] text-xs">
                    No matching assets found
                  </div>
                ) : (
                  matchingAssets.map((asset) => {
                    const isPositive = asset.change_24h_pct >= 0;
                    return (
                      <button
                        key={asset.symbol}
                        onClick={() => handleSelectAsset(asset.symbol)}
                        className="w-full text-left p-3 hover:bg-[#171f33] transition-colors flex items-center justify-between"
                      >
                        <div className="flex flex-col">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[#dae2fd]">{asset.symbol}</span>
                            <span className="text-[10px] text-[#908f9e] font-sans truncate max-w-[110px]">
                              {asset.name}
                            </span>
                          </div>
                          <span className="text-[9px] text-[#818cf8] uppercase mt-0.5">
                            {asset.asset_type.replace("_", " ")}
                          </span>
                        </div>

                        <div className="flex flex-col items-end">
                          <span className="font-bold text-[#dae2fd]">
                            {formatCurrency(asset.current_price)}
                          </span>
                          <span
                            className={`flex items-center text-[10px] font-bold ${
                              isPositive ? "text-[#4edea3]" : "text-[#ffb2b7]"
                            }`}
                          >
                            {formatPercent(asset.change_24h_pct, 2, true)}
                          </span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>

          {/* Dark / Light Mode Toggle Button */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-[#131b2e] text-[#818cf8] border border-[#2d3449] hover:border-[#818cf8]/40 transition-all shadow"
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-500" />}
          </button>
        </div>
      </div>
    </header>
  );
};
