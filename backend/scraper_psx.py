import datetime
import yfinance as yf
import pandas as pd
from database import SessionLocal, init_db, Fund, FundNAV

# ==========================================
# 1. DEFINE THE STOCKS WE WANT TO FETCH
# ==========================================
# We will track the top 5 companies on the Pakistan Stock Exchange.
# Yahoo Finance tracks them using the ".KA" suffix (Karachi).
TICKERS = {
    "Systems Limited": "SYS.KA",
    "Meezan Bank": "MEBL.KA",
    "Hub Power Company": "HUBC.KA",
    "Engro Corporation": "ENGRO.KA",
    "Oil & Gas Development Co": "OGDC.KA"
}

def scrape_and_save_stocks():
    # We want 5 years of historical data
    # yfinance makes this incredibly easy with period="5y"
    print("Connecting to Yahoo Finance to fetch 5 years of PSX stock data...")
    
    all_stock_data = []
    db = SessionLocal()
    
    try:
        # Initialize SQLite database tables first
        init_db()
        
        for company_name, ticker_symbol in TICKERS.items():
            print(f"Fetching data for {company_name} ({ticker_symbol})...")
            
            # Fetch the data using yfinance
            ticker_obj = yf.Ticker(ticker_symbol)
            # period="5y" gets exactly 5 years of daily closing prices
            df_history = ticker_obj.history(period="5y")
            
            if df_history.empty:
                print(f"Warning: No data returned for {ticker_symbol}")
                continue
                
            # Reset index so that the Date becomes a normal column instead of a row header
            df_history = df_history.reset_index()
            
            # ----------------------------------------------------
            # A. Prepare the data for Excel
            # ----------------------------------------------------
            for _, row in df_history.iterrows():
                all_stock_data.append({
                    "Date": row["Date"].strftime("%Y-%m-%d"),
                    "Company Name": company_name,
                    "Ticker Symbol": ticker_symbol,
                    "Open Price": round(row["Open"], 2),
                    "High Price": round(row["High"], 2),
                    "Low Price": round(row["Low"], 2),
                    "Close Price": round(row["Close"], 2),
                    "Volume": int(row["Volume"])
                })
                
            # ----------------------------------------------------
            # B. Save the data to SQLite Database (for charts)
            # ----------------------------------------------------
            # To show these in our dashboard charts, we save them as "Funds"
            # so the existing frontend doesn't need to be rewritten!
            fund = db.query(Fund).filter(Fund.name == company_name).first()
            if not fund:
                fund = Fund(
                    name=company_name,
                    category="PSX Stock",
                    risk_level="High",
                    is_islamic=(company_name in ["Meezan Bank", "Systems Limited", "Hub Power Company"]),
                    fund_size_mkr=10000.0
                )
                db.add(fund)
                db.commit()
                db.refresh(fund)
                
            # Save daily closing prices into SQLite
            for _, row in df_history.iterrows():
                nav_date = row["Date"].date()
                # Check if it already exists to avoid duplicates
                existing_nav = db.query(FundNAV).filter(
                    FundNAV.fund_id == fund.id,
                    FundNAV.date == nav_date
                ).first()
                
                if not existing_nav:
                    new_nav = FundNAV(
                        fund_id=fund.id,
                        date=nav_date,
                        nav=round(row["Close"], 2)
                    )
                    db.add(new_nav)
            db.commit()

        # ----------------------------------------------------
        # C. Export to Excel File (.xlsx)
        # ----------------------------------------------------
        if all_stock_data:
            df_excel = pd.DataFrame(all_stock_data)
            excel_filename = "psx_stock_data.xlsx"
            
            # pandas writes to Excel instantly using the openpyxl engine
            df_excel.to_excel(excel_filename, index=False, sheet_name="PSX Stocks 5-Year History")
            print(f"\nSuccess! 5 years of stock data saved to Excel file: {excel_filename}")
            print(f"Total rows exported: {len(df_excel)}")
            
    except Exception as e:
        print(f"Error occurred during stock scraping: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    scrape_and_save_stocks()& "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" scraper_psx.py