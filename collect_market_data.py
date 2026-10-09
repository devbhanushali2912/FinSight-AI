
import time
import yfinance as yf
import pandas as pd

companies = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Larsen & Toubro": "LT.NS",
    "ITC": "ITC.NS",
    "Tata Motors": "TMPV.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
}

frames = []

for company, ticker in companies.items():
    print(f"Downloading {company} ({ticker})...")

    try:
        history = yf.Ticker(ticker).history(
            period="1y",
            interval="1d",
            auto_adjust=True,
        )

        if history.empty:
            print("  WARNING: No data returned.")
            continue

        history = history.reset_index()
        history["Company"] = company
        history["Ticker"] = ticker

        frames.append(history)
        print(f"  Retrieved {len(history)} rows.")

    except Exception as exc:
        print(f"  ERROR: {exc}")

    time.sleep(1)

if not frames:
    raise RuntimeError("No market data was collected.")

data = pd.concat(frames, ignore_index=True)

data["Date"] = pd.to_datetime(data["Date"], utc=True)
data["Date"] = data["Date"].dt.strftime("%Y-%m-%d")

columns = [
    "Date", "Company", "Ticker",
    "Open", "High", "Low", "Close", "Volume"
]

data = data[columns].sort_values(["Ticker", "Date"])

data.to_csv("market_prices.csv", index=False)

print("\n--- COLLECTION SUMMARY ---")
print(f"Companies collected: {data['Ticker'].nunique()}")
print(f"Total price records: {len(data)}")
print(f"Date range: {data['Date'].min()} to {data['Date'].max()}")
print("Saved to market_prices.csv")
print("\nRecords per company:")
print(data.groupby("Company").size().to_string())
