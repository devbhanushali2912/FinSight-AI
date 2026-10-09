
import numpy as np
import pandas as pd

df = pd.read_csv("market_prices.csv", parse_dates=["Date"])
df = df.sort_values(["Ticker", "Date"])

# Calculate metrics separately for each company.
grouped = df.groupby("Ticker", group_keys=False)

df["Daily_Return"] = grouped["Close"].pct_change()

df["MA_20"] = grouped["Close"].transform(
    lambda s: s.rolling(20).mean()
)

df["MA_50"] = grouped["Close"].transform(
    lambda s: s.rolling(50).mean()
)

def calculate_metrics(group):
    prices = group["Close"].dropna()
    returns = prices.pct_change().dropna()

    if prices.empty or returns.empty:
        return pd.Series(dtype="float64")

    running_peak = prices.cummax()
    drawdown = prices / running_peak - 1

    annual_return = (prices.iloc[-1] / prices.iloc[0]) ** (
        252 / max(len(prices) - 1, 1)
    ) - 1

    return pd.Series({
        "Start_Date": group["Date"].min().date().isoformat(),
        "End_Date": group["Date"].max().date().isoformat(),
        "Observations": len(prices),
        "Period_Return_%": (
            prices.iloc[-1] / prices.iloc[0] - 1
        ) * 100,
        "Annualized_Return_%": annual_return * 100,
        "Annualized_Volatility_%": (
            returns.std(ddof=1) * np.sqrt(252) * 100
        ),
        "Maximum_Drawdown_%": drawdown.min() * 100,
        "Latest_Close": prices.iloc[-1],
        "MA_20": prices.tail(20).mean(),
        "MA_50": prices.tail(50).mean(),
    })

summary = (
    df.groupby(["Company", "Ticker"])
    .apply(calculate_metrics, include_groups=False)
    .reset_index()
)

summary.to_csv("market_analytics_results.csv", index=False)
df.to_csv("market_prices_with_indicators.csv", index=False)

print("MARKET ANALYTICS SUMMARY")
print(summary.round(2).to_string(index=False))
print("\nSaved market_analytics_results.csv")
print("Saved market_prices_with_indicators.csv")
