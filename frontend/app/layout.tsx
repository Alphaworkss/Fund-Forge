import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/navigation/Navbar";
import { TickerRibbon } from "@/components/navigation/TickerRibbon";

export const metadata: Metadata = {
  title: "SarmayaSaaz - AI Financial Price Forecasting & Market Intelligence",
  description:
    "AI-driven multi-asset financial price forecasting, SHAP explainability, model analytics and market intelligence platform supporting Stocks, Cryptocurrencies, Mutual Funds and Commodities.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b1326] text-[#dae2fd] antialiased min-h-screen flex flex-col font-sans">
        <Navbar />
        <TickerRibbon />
        <main className="flex-1 pt-28 px-4 sm:px-6 max-w-[1440px] w-full mx-auto pb-12">
          {children}
        </main>
      </body>
    </html>
  );
}
