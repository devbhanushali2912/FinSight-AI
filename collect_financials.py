
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

all_statements = []

for company, ticker in companies.items():
    print(f"\nCollecting: {company} ({ticker})")
    stock = yf.Ticker(ticker)

    for statement_name in ["income_stmt", "balance_sheet", "cashflow"]:
        try:
            statement = getattr(stock, statement_name)

            print(
                f"  {statement_name}: "
                f"{type(statement).__name__}, "
                f"shape={getattr(statement, 'shape', None)}"
            )

            if not isinstance(statement, pd.DataFrame) or statement.empty:
                print("  SKIPPED: Not a non-empty DataFrame.")
                continue

            long_df = (
                statement.rename_axis("Metric")
                .rename_axis("Period", axis=1)
                .stack(future_stack=True)
                .rename("Value")
                .reset_index()
                )
            

            long_df["Company"] = company
            long_df["Ticker"] = ticker
            long_df["Statement"] = statement_name
            all_statements.append(long_df)

            print(f"  SAVED IN MEMORY: {len(long_df)} rows")

        except Exception as exc:
            print(
                f"  ERROR in {statement_name}: "
                f"{type(exc).__name__}: {exc}"
            )

    time.sleep(1)

if not all_statements:
    raise RuntimeError(
        "No statements collected. Review the per-statement errors above."
    )

data = pd.concat(all_statements, ignore_index=True)
data = data[
    ["Company", "Ticker", "Statement", "Metric", "Period", "Value"]
]
data["Period"] = pd.to_datetime(data["Period"]).dt.strftime("%Y-%m-%d")
data["Value"] = pd.to_numeric(data["Value"], errors="coerce")
data = data.sort_values(
    ["Company", "Statement", "Metric", "Period"]
)

data.to_csv("financial_statements.csv", index=False)

print("\nCOLLECTION COMPLETE")
print("Rows:", len(data))
print("Companies:", data["Company"].nunique())
print("Statements:", data["Statement"].nunique())
print("Output: financial_statements.csv")
print("\nRows per statement:")
print(data.groupby("Statement").size())
