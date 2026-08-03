import pandas as pd

def validate_excel_data():
    file_path = "psx_stock_data.xlsx"
    print(f"Loading {file_path} for validation...")
    
    # Load the Excel file we created
    df = pd.read_excel(file_path)
    
    print("\n--- Starting Data Validation ---")
    
    # Check 1: Do we have all columns?
    required_cols = ["Date", "Company Name", "Ticker Symbol", "Close Price", "Volume"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if not missing_cols:
        print("✅ Check 1: All required columns are present.")
    else:
        print(f"❌ Check 1 failed: Missing columns: {missing_cols}")

    # Check 2: Are there any empty (null) values in prices?
    null_count = df["Close Price"].isnull().sum()
    if null_count == 0:
        print("✅ Check 2: No missing (null) values found in closing prices.")
    else:
        print(f"❌ Check 2 failed: Found {null_count} empty price cells.")

    # Check 3: Are all stock prices positive? (Stock prices cannot be negative or zero)
    invalid_prices = df[df["Close Price"] <= 0]
    if invalid_prices.empty:
        print("✅ Check 3: All stock prices are valid positive numbers.")
    else:
        print(f"❌ Check 3 failed: Found negative or zero prices for: {invalid_prices['Company Name'].unique()}")

    # Check 4: Do we have enough data (5 years)?
    # 5 years of daily data should be around 1,200 rows per stock.
    # Total rows for 5 stocks should be around 6,000.
    total_rows = len(df)
    print(f"✅ Check 4: Data length is {total_rows} rows.")
    if total_rows > 5000:
        print("   -> Looks good! We have over 5 years of daily records.")
    else:
        print("   -> Warning: Data seems too short for 5 years.")

    print("\n--- Validation Complete ---")

if __name__ == "__main__":
    validate_excel_data()