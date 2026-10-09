
import pandas as pd
import numpy as np

SOURCE = "financial_statements.csv"
OUTPUT = "financial_ratios.csv"

df = pd.read_csv(SOURCE)
df["Period"] = pd.to_datetime(df["Period"], errors="coerce")
df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

def get_metric(statement_df, names):
    """Return the first exact metric match; do not substitute missing values."""
    for name in names:
        rows = statement_df[
            statement_df["Metric"].astype(str).str.strip().str.casefold()
            == name.casefold()
        ]
        if not rows.empty:
            return rows.iloc[0]["Value"]
    return np.nan

records = []

for (company, ticker, period), group in df.groupby(
    ["Company", "Ticker", "Period"]
):
    income = group[group["Statement"] == "income_stmt"]
    balance = group[group["Statement"] == "balance_sheet"]
    cashflow = group[group["Statement"] == "cashflow"]

    revenue = get_metric(income, ["Total Revenue", "Operating Revenue"])
    net_income = get_metric(income, ["Net Income", "Net Income Common Stockholders"])
    assets = get_metric(balance, ["Total Assets"])
    equity = get_metric(balance, [
        "Stockholders Equity",
        "Total Equity Gross Minority Interest",
        "Common Stock Equity",
    ])
    debt = get_metric(balance, ["Total Debt"])
    operating_cash_flow = get_metric(cashflow, ["Operating Cash Flow"])

    def divide(a, b):
        if pd.isna(a) or pd.isna(b) or b == 0:
            return np.nan
        return a / b

    records.append({
        "Company": company,
        "Ticker": ticker,
        "Period": period,
        "Sector Group": (
            "Banking" if company in ["HDFC Bank", "ICICI Bank"]
            else "Non-bank"
        ),
        "Revenue": revenue,
        "Net Income": net_income,
        "Total Assets": assets,
        "Total Equity": equity,
        "Total Debt": debt,
        "Operating Cash Flow": operating_cash_flow,
        "Net Profit Margin %": divide(net_income, revenue) * 100,
        "Return on Assets %": divide(net_income, assets) * 100,
        "Debt to Equity": divide(debt, equity),
        "Operating Cash Flow / Net Income": divide(
            operating_cash_flow, net_income
        ),
    })

ratios = pd.DataFrame(records).sort_values(["Company", "Period"])

# Revenue growth requires a prior reporting period for the same company.
ratios["Revenue Growth %"] = (
    ratios.groupby("Company")["Revenue"].pct_change(fill_method=None) * 100
)

ratios.to_csv(OUTPUT, index=False)

print("Saved:", OUTPUT)
print("Rows:", len(ratios))
print("Companies:", ratios["Company"].nunique())
print("\nAvailable values:")
print(ratios.notna().sum().to_string())

print("\nLatest reporting-period snapshot:")
latest = (
    ratios.sort_values("Period")
    .groupby("Company")
    .tail(1)
    .sort_values("Company")
)
print(latest[[
    "Company", "Period", "Revenue Growth %",
    "Net Profit Margin %", "Return on Assets %",
    "Debt to Equity"
]].to_string(index=False))

print("\nNote: These are preliminary screening metrics, not investment advice.")
