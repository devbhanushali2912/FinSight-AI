
import pandas as pd

df = pd.read_csv("financial_ratios.csv")
df["Period"] = pd.to_datetime(df["Period"], errors="coerce")
df = df.sort_values(["Company", "Period"])

companies_to_review = [
    "Bharti Airtel",
    "ITC",
    "Tata Motors",
]

columns = [
    "Company",
    "Period",
    "Revenue",
    "Net Income",
    "Net Profit Margin %",
    "Revenue Growth %",
    "Total Assets",
    "Total Equity",
    "Total Debt",
]

for company in companies_to_review:
    print(f"\n{'=' * 70}")
    print(company)
    print(f"{'=' * 70}")

    subset = df[df["Company"] == company]

    available = [col for col in columns if col in subset.columns]
    print(subset[available].to_string(index=False))

print("\nReview complete.")
print(
    "Compare year-by-year values before treating any flag as a real "
    "financial deterioration signal."
)
