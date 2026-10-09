
import pandas as pd
from pathlib import Path

file_path = Path("financial_statements.csv")

if not file_path.exists():
    raise FileNotFoundError(f"Missing file: {file_path}")

df = pd.read_csv(file_path)

required_columns = [
    "Company", "Ticker", "Statement",
    "Metric", "Period", "Value"
]

print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())

missing_columns = set(required_columns) - set(df.columns)
if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

df["Period"] = pd.to_datetime(df["Period"], errors="coerce")
df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

print("\nCompanies:", df["Company"].nunique())
print("\nRows per company:")
print(df.groupby("Company").size())

print("\nRows per statement:")
print(df.groupby("Statement").size())

print("\nMissing values:")
print(df[required_columns].isna().sum())

print("\nDuplicate records:", df.duplicated(
    subset=["Company", "Statement", "Metric", "Period"]
).sum())

print("\nReporting periods:")
print(df.groupby("Company")["Period"].agg(["min", "max"]))

print("\nExample records:")
print(df.head(10).to_string(index=False))

print("\nValidation inspection complete.")
