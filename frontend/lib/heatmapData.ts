export type MetricType = "overall_score" | "mae" | "rmse" | "mape_pct" | "r2_score" | "directional_accuracy_pct";

export interface MetricDefinition {
  id: MetricType;
  label: string;
  shortLabel: string;
  higherIsBetter: boolean;
  unit: string;
  description: string;
}

export const METRIC_DEFINITIONS: Record<MetricType, MetricDefinition> = {
  overall_score: {
    id: "overall_score",
    label: "Overall Score",
    shortLabel: "Score",
    higherIsBetter: true,
    unit: "/ 100",
    description: "Composite evaluation score balancing accuracy, error minimization, and directional precision.",
  },
  mae: {
    id: "mae",
    label: "Mean Absolute Error (MAE)",
    shortLabel: "MAE",
    higherIsBetter: false,
    unit: "$",
    description: "Average absolute difference between predicted and actual price targets. Lower is better.",
  },
  rmse: {
    id: "rmse",
    label: "Root Mean Squared Error (RMSE)",
    shortLabel: "RMSE",
    higherIsBetter: false,
    unit: "$",
    description: "Square root of mean squared prediction errors, penalizing larger outliers. Lower is better.",
  },
  mape_pct: {
    id: "mape_pct",
    label: "Mean Absolute Percentage Error (MAPE)",
    shortLabel: "MAPE",
    higherIsBetter: false,
    unit: "%",
    description: "Average percentage error relative to actual price levels. Lower is better.",
  },
  r2_score: {
    id: "r2_score",
    label: "Coefficient of Determination (R²)",
    shortLabel: "R²",
    higherIsBetter: true,
    unit: "",
    description: "Proportion of price variance explained by the model (0.00 to 1.00). Higher is better.",
  },
  directional_accuracy_pct: {
    id: "directional_accuracy_pct",
    label: "Directional Accuracy",
    shortLabel: "Direction",
    higherIsBetter: true,
    unit: "%",
    description: "Percentage of price trend movements correctly predicted (bullish vs bearish). Higher is better.",
  },
};

export const AVAILABLE_MODELS = [
  "PatchTST",
  "TFT",
  "LightGBM",
  "XGBoost",
  "Random Forest",
  "ARIMA",
] as const;

export type ModelName = (typeof AVAILABLE_MODELS)[number];

export type HorizonType = "1d" | "7d" | "14d" | "30d" | "90d";

export interface CellMetrics {
  overall_score: number;
  mae: number;
  rmse: number;
  mape_pct: number;
  r2_score: number;
  directional_accuracy_pct: number;
  training_period: string;
  evaluation_period: string;
  isAvailable: boolean;
}

export interface AssetHeatmapEntry {
  symbol: string;
  name: string;
  assetClass: "crypto" | "stock" | "mutual_fund" | "commodity";
  category: string;
  currentPrice: number;
  models: Record<ModelName, Record<HorizonType, CellMetrics | null>>;
}

export interface CategoryGroup {
  id: string;
  name: string;
  assetClass: "crypto" | "stock" | "mutual_fund" | "commodity";
  assetCount: number;
  assets: AssetHeatmapEntry[];
}

export interface AssetClassGroup {
  id: string;
  name: string;
  categories: CategoryGroup[];
}

// Specified Exact 10 Crypto Categories
export const CRYPTO_CATEGORIES = [
  "Layer 1 Blockchain",
  "Layer 2 & Scaling",
  "DeFi",
  "Payments & RWA",
  "AI & Data",
  "Meme Coin",
  "Gaming, Metaverse & NFT",
  "Infrastructure & Interoperability",
  "Privacy Coin",
  "Exchange & Utility Token",
] as const;

// Seed Generator for Realistic Multi-Model Quantitative Evaluation Metrics
function generateModelMetrics(
  symbol: string,
  price: number,
  model: ModelName,
  horizon: HorizonType,
  assetClass: string
): CellMetrics | null {
  // ARIMA is unavailable for certain exotic altcoins/meme coins
  if (model === "ARIMA" && (symbol === "PEPE" || symbol === "WIF" || symbol === "BONK")) {
    return null;
  }

  // Model strength modifiers
  let baseScore = 80;
  if (model === "PatchTST") baseScore = 90;
  if (model === "TFT") baseScore = 88;
  if (model === "XGBoost") baseScore = 86;
  if (model === "LightGBM") baseScore = 85;
  if (model === "Random Forest") baseScore = 81;
  if (model === "ARIMA") baseScore = 73;

  // Horizon penalty (longer horizons are harder to predict)
  const horizonPenalty =
    horizon === "1d" ? 0 : horizon === "7d" ? 2 : horizon === "14d" ? 4 : horizon === "30d" ? 7 : 12;

  // Symbol hash variation
  const hash = symbol.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const symbolMod = (hash % 11) - 5; // -5 to +5

  const score = Math.max(50, Math.min(98, baseScore - horizonPenalty + symbolMod));

  // Derive realistic financial error metrics
  const errorScale = (100 - score) / 100;
  const mae = roundTwo(price * (0.01 + errorScale * 0.04));
  const rmse = roundTwo(mae * 1.32);
  const mape = roundTwo(1.2 + errorScale * 4.8);
  const r2 = roundTwo(Math.max(0.4, 0.95 - errorScale * 0.45));
  const dirAcc = roundTwo(Math.min(94, Math.max(52, score * 0.92)));

  return {
    overall_score: score,
    mae,
    rmse,
    mape_pct: mape,
    r2_score: r2,
    directional_accuracy_pct: dirAcc,
    training_period: "2021-01 to 2026-06",
    evaluation_period: `Holdout Test (${horizon.toUpperCase()})`,
    isAvailable: true,
  };
}

function roundTwo(val: number): number {
  return Math.round(val * 100) / 100;
}

// Master Dataset Builder
export function getMasterHeatmapData(): AssetClassGroup[] {
  const horizons: HorizonType[] = ["1d", "7d", "14d", "30d", "90d"];

  const buildAssetEntry = (
    symbol: string,
    name: string,
    assetClass: "crypto" | "stock" | "mutual_fund" | "commodity",
    category: string,
    price: number
  ): AssetHeatmapEntry => {
    const modelsData = {} as Record<ModelName, Record<HorizonType, CellMetrics | null>>;
    AVAILABLE_MODELS.forEach((m) => {
      modelsData[m] = {} as Record<HorizonType, CellMetrics | null>;
      horizons.forEach((h) => {
        modelsData[m][h] = generateModelMetrics(symbol, price, m, h, assetClass);
      });
    });

    return {
      symbol,
      name,
      assetClass,
      category,
      currentPrice: price,
      models: modelsData,
    };
  };

  // 1. CRYPTO (10 Exact Specified Categories)
  const cryptoCategories: CategoryGroup[] = [
    {
      id: "cat-crypto-l1",
      name: "Layer 1 Blockchain",
      assetClass: "crypto",
      assetCount: 5,
      assets: [
        buildAssetEntry("BTC", "Bitcoin", "crypto", "Layer 1 Blockchain", 118420.50),
        buildAssetEntry("ETH", "Ethereum", "crypto", "Layer 1 Blockchain", 3850.75),
        buildAssetEntry("SOL", "Solana", "crypto", "Layer 1 Blockchain", 185.30),
        buildAssetEntry("ADA", "Cardano", "crypto", "Layer 1 Blockchain", 0.42),
        buildAssetEntry("AVAX", "Avalanche", "crypto", "Layer 1 Blockchain", 28.50),
      ],
    },
    {
      id: "cat-crypto-l2",
      name: "Layer 2 & Scaling",
      assetClass: "crypto",
      assetCount: 4,
      assets: [
        buildAssetEntry("POL", "Polygon", "crypto", "Layer 2 & Scaling", 0.54),
        buildAssetEntry("ARB", "Arbitrum", "crypto", "Layer 2 & Scaling", 0.62),
        buildAssetEntry("OP", "Optimism", "crypto", "Layer 2 & Scaling", 1.85),
        buildAssetEntry("MNT", "Mantle", "crypto", "Layer 2 & Scaling", 0.78),
      ],
    },
    {
      id: "cat-crypto-defi",
      name: "DeFi",
      assetClass: "crypto",
      assetCount: 4,
      assets: [
        buildAssetEntry("UNI", "Uniswap", "crypto", "DeFi", 7.80),
        buildAssetEntry("AAVE", "Aave", "crypto", "DeFi", 114.20),
        buildAssetEntry("MKR", "Maker", "crypto", "DeFi", 2450.00),
        buildAssetEntry("CRV", "Curve DAO", "crypto", "DeFi", 0.34),
      ],
    },
    {
      id: "cat-crypto-rwa",
      name: "Payments & RWA",
      assetClass: "crypto",
      assetCount: 3,
      assets: [
        buildAssetEntry("XRP", "XRP", "crypto", "Payments & RWA", 0.62),
        buildAssetEntry("XLM", "Stellar Lumens", "crypto", "Payments & RWA", 0.11),
        buildAssetEntry("ONDO", "Ondo Finance", "crypto", "Payments & RWA", 0.88),
      ],
    },
    {
      id: "cat-crypto-ai",
      name: "AI & Data",
      assetClass: "crypto",
      assetCount: 3,
      assets: [
        buildAssetEntry("NEAR", "NEAR Protocol", "crypto", "AI & Data", 5.20),
        buildAssetEntry("FET", "Artificial Superintelligence", "crypto", "AI & Data", 1.45),
        buildAssetEntry("RENDER", "Render Token", "crypto", "AI & Data", 6.10),
      ],
    },
    {
      id: "cat-crypto-meme",
      name: "Meme Coin",
      assetClass: "crypto",
      assetCount: 3,
      assets: [
        buildAssetEntry("DOGE", "Dogecoin", "crypto", "Meme Coin", 0.12),
        buildAssetEntry("SHIB", "Shiba Inu", "crypto", "Meme Coin", 0.000018),
        buildAssetEntry("PEPE", "Pepe", "crypto", "Meme Coin", 0.000009),
      ],
    },
    {
      id: "cat-crypto-gaming",
      name: "Gaming, Metaverse & NFT",
      assetClass: "crypto",
      assetCount: 3,
      assets: [
        buildAssetEntry("GALA", "Gala", "crypto", "Gaming, Metaverse & NFT", 0.024),
        buildAssetEntry("IMX", "Immutable X", "crypto", "Gaming, Metaverse & NFT", 1.55),
        buildAssetEntry("SAND", "The Sandbox", "crypto", "Gaming, Metaverse & NFT", 0.32),
      ],
    },
    {
      id: "cat-crypto-infra",
      name: "Infrastructure & Interoperability",
      assetClass: "crypto",
      assetCount: 3,
      assets: [
        buildAssetEntry("ATOM", "Cosmos", "crypto", "Infrastructure & Interoperability", 5.40),
        buildAssetEntry("LINK", "Chainlink", "crypto", "Infrastructure & Interoperability", 14.20),
        buildAssetEntry("TIA", "Celestia", "crypto", "Infrastructure & Interoperability", 6.80),
      ],
    },
    {
      id: "cat-crypto-privacy",
      name: "Privacy Coin",
      assetClass: "crypto",
      assetCount: 2,
      assets: [
        buildAssetEntry("XMR", "Monero", "crypto", "Privacy Coin", 162.40),
        buildAssetEntry("ZEC", "Zcash", "crypto", "Privacy Coin", 32.10),
      ],
    },
    {
      id: "cat-crypto-exchange",
      name: "Exchange & Utility Token",
      assetClass: "crypto",
      assetCount: 2,
      assets: [
        buildAssetEntry("BNB", "BNB", "crypto", "Exchange & Utility Token", 580.40),
        buildAssetEntry("OKB", "OKB", "crypto", "Exchange & Utility Token", 41.80),
      ],
    },
  ];

  // 2. STOCKS (Sectors)
  const stockCategories: CategoryGroup[] = [
    {
      id: "cat-stock-tech",
      name: "Technology",
      assetClass: "stock",
      assetCount: 4,
      assets: [
        buildAssetEntry("NVDA", "NVIDIA Corporation", "stock", "Technology", 128.90),
        buildAssetEntry("AAPL", "Apple Inc.", "stock", "Technology", 224.50),
        buildAssetEntry("MSFT", "Microsoft Corporation", "stock", "Technology", 448.20),
        buildAssetEntry("GOOGL", "Alphabet Inc.", "stock", "Technology", 175.40),
      ],
    },
    {
      id: "cat-stock-consumer",
      name: "Consumer Cyclical",
      assetClass: "stock",
      assetCount: 2,
      assets: [
        buildAssetEntry("AMZN", "Amazon.com Inc.", "stock", "Consumer Cyclical", 186.40),
        buildAssetEntry("TSLA", "Tesla Inc.", "stock", "Consumer Cyclical", 210.20),
      ],
    },
    {
      id: "cat-stock-[#fin]",
      name: "Financials",
      assetClass: "stock",
      assetCount: 2,
      assets: [
        buildAssetEntry("JPM", "JPMorgan Chase & Co.", "stock", "Financials", 212.80),
        buildAssetEntry("BAC", "Bank of America Corp.", "stock", "Financials", 39.40),
      ],
    },
  ];

  // 3. MUTUAL FUNDS
  const fundCategories: CategoryGroup[] = [
    {
      id: "cat-fund-equity",
      name: "Equity Growth",
      assetClass: "mutual_fund",
      assetCount: 2,
      assets: [
        buildAssetEntry("GROWTH_FUND", "SarmayaSaaz Global Tech Growth Fund", "mutual_fund", "Equity Growth", 54.80),
        buildAssetEntry("INDEX_FUND", "SarmayaSaaz S&P 500 Index Fund", "mutual_fund", "Equity Growth", 112.40),
      ],
    },
    {
      id: "cat-fund-[#inc]",
      name: "Fixed Income & Bond",
      assetClass: "mutual_fund",
      assetCount: 2,
      assets: [
        buildAssetEntry("INCOME_FUND", "SarmayaSaaz High Yield Bond & Income Fund", "mutual_fund", "Fixed Income & Bond", 28.15),
        buildAssetEntry("CASH_FUND", "SarmayaSaaz Capital Preservation Fund", "mutual_fund", "Fixed Income & Bond", 10.05),
      ],
    },
    {
      id: "cat-fund-shariah",
      name: "Islamic / Shariah-Compliant",
      assetClass: "mutual_fund",
      assetCount: 1,
      assets: [
        buildAssetEntry("ISLAMIC_FUND", "SarmayaSaaz Shariah Equity Fund", "mutual_fund", "Islamic / Shariah-Compliant", 42.60),
      ],
    },
  ];

  // 4. COMMODITIES (Direct Assets)
  const commodityCategories: CategoryGroup[] = [
    {
      id: "cat-commodity-all",
      name: "Precious Metals & Energy",
      assetClass: "commodity",
      assetCount: 5,
      assets: [
        buildAssetEntry("GOLD", "Gold Spot", "commodity", "Precious Metals & Energy", 2435.80),
        buildAssetEntry("SILVER", "Silver Spot", "commodity", "Precious Metals & Energy", 28.40),
        buildAssetEntry("CRUDE_OIL", "WTI Crude Oil", "commodity", "Precious Metals & Energy", 78.45),
        buildAssetEntry("NATURAL_GAS", "Natural Gas", "commodity", "Precious Metals & Energy", 2.35),
        buildAssetEntry("COPPER", "Copper High Grade", "commodity", "Precious Metals & Energy", 4.15),
      ],
    },
  ];

  return [
    { id: "crypto", name: "Cryptocurrencies", categories: cryptoCategories },
    { id: "stock", name: "Stocks", categories: stockCategories },
    { id: "mutual_fund", name: "Mutual Funds", categories: fundCategories },
    { id: "commodity", name: "Commodities", categories: commodityCategories },
  ];
}

// Compute Aggregated Median Performance Rows for All 4 Asset Classes
export function getOverallAssetClassSummaryRows(data: AssetClassGroup[]): AssetHeatmapEntry[] {
  const horizons: HorizonType[] = ["1d", "7d", "14d", "30d", "90d"];

  return data.map((acGroup) => {
    // Collect all assets under this asset class
    const allClassAssets: AssetHeatmapEntry[] = [];
    acGroup.categories.forEach((cat) => {
      cat.assets.forEach((ast) => allClassAssets.push(ast));
    });

    const modelsData = {} as Record<ModelName, Record<HorizonType, CellMetrics | null>>;

    AVAILABLE_MODELS.forEach((m) => {
      modelsData[m] = {} as Record<HorizonType, CellMetrics | null>;
      horizons.forEach((h) => {
        // Collect metrics across all assets in this class for model m and horizon h
        const scores: number[] = [];
        const maes: number[] = [];
        const rmses: number[] = [];
        const mapes: number[] = [];
        const r2s: number[] = [];
        const dirAccs: number[] = [];

        allClassAssets.forEach((ast) => {
          const cell = ast.models[m][h];
          if (cell && cell.isAvailable) {
            scores.push(cell.overall_score);
            maes.push(cell.mae);
            rmses.push(cell.rmse);
            mapes.push(cell.mape_pct);
            r2s.push(cell.r2_score);
            dirAccs.push(cell.directional_accuracy_pct);
          }
        });

        if (scores.length === 0) {
          modelsData[m][h] = null;
        } else {
          modelsData[m][h] = {
            overall_score: roundTwo(median(scores)),
            mae: roundTwo(median(maes)),
            rmse: roundTwo(median(rmses)),
            mape_pct: roundTwo(median(mapes)),
            r2_score: roundTwo(median(r2s)),
            directional_accuracy_pct: roundTwo(median(dirAccs)),
            training_period: "2021-01 to 2026-06",
            evaluation_period: `Asset Class Aggregated (${h.toUpperCase()})`,
            isAvailable: true,
          };
        }
      });
    });

    return {
      symbol: acGroup.name.toUpperCase().slice(0, 6),
      name: `${acGroup.name} (Overall Asset Class)`,
      assetClass: acGroup.id as any,
      category: "Asset Class Aggregate",
      currentPrice: 0,
      models: modelsData,
    };
  });
}

function median(arr: number[]): number {
  if (arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}
