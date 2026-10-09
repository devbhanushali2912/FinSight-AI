
import pandas as pd

df = pd.read_csv("market_prices.csv")

print("DATASET SHAPE:", df.shape)
print("\nMISSING VALUES:")
print(df.isna().sum().to_string())

print("\nDUPLICATE COMPANY-DATE RECORDS:")
duplicates = df.duplicated(subset=["Ticker", "Date"]).sum()
print(duplicates)

price_columns = ["Open", "High", "Low", "Close"]

print("\nNON-POSITIVE PRICES:")
print((df[price_columns] <= 0).sum().to_string())

print("\nINVALID OHLC RELATIONSHIPS:")
invalid = (
    (df["High"] < df[["Open", "Low", "Close"]].max(axis=1))
    | (df["Low"] > df[["Open", "High", "Close"]].min(axis=1))
)
print(int(invalid.sum()))

print("\nCOMPANY RECORD COUNTS:")
print(df.groupby("Ticker").size().to_string())

if (
    df.isna().any().any()
    or duplicates > 0
    or (df[price_columns] <= 0).any().any()
    or invalid.any()
):
    print("\nREVIEW REQUIRED: Investigate the reported data-quality issues.")
else:
    print("\nPASS: Basic data-quality checks passed.")
