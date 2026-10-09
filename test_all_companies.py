
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

results = []

for company, ticker in companies.items():
    try:
        history = yf.Ticker(ticker).history(
            period="1mo",
            interval="1d"
        )

        if history.empty:
            results.append({
                "Company": company,
                "Ticker": ticker,
                "Status": "NO DATA",
                "Rows": 0,
            })
        else:
            results.append({
                "Company": company,
                "Ticker": ticker,
                "Status": "SUCCESS",
                "Rows": len(history),
            })

    except Exception as exc:
        results.append({
            "Company": company,
            "Ticker": ticker,
            "Status": f"ERROR: {str(exc)[:100]}",
            "Rows": 0,
        })

df = pd.DataFrame(results)
print(df.to_string(index=False))

df.to_csv("market_data_test_results.csv", index=False)
print("\nSaved results to market_data_test_results.csv")
print(f"Successful companies: {(df['Status'] == 'SUCCESS').sum()}/10")
