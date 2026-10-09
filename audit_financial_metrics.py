
import pandas as pd

df = pd.read_csv("financial_statements.csv")

targets = {
    "income_stmt": [
        "Total Revenue",
        "Operating Revenue",
        "Net Income",
        "Net Income Common Stockholders",
    ],
    "balance_sheet": [
        "Total Assets",
        "Stockholders Equity",
        "Total Stockholder Equity",
        "Common Stock Equity",
        "Total Debt",
    ],
    "cashflow": [
        "Operating Cash Flow",
        "Cash Flow From Continuing Operating Activities",
    ],
}

for statement, candidates in targets.items():
    subset = df[df["Statement"] == statement]

    print(f"\n{'=' * 65}")
    print(f"STATEMENT: {statement}")
    print(f"{'=' * 65}")

    for candidate in candidates:
        matches = subset[
            subset["Metric"].str.strip().str.casefold()
            == candidate.casefold()
        ]

        if matches.empty:
            print(f"\n{candidate}: NOT FOUND")
            continue

        print(f"\n{candidate}:")
        print(
            matches.groupby("Company")["Value"]
            .count()
            .to_string()
        )

        print("Example values:")
        print(
            matches[matches["Company"] == "Reliance Industries"][
                ["Period", "Value"]
            ].to_string(index=False)
        )

print("\nMetric audit complete.")
