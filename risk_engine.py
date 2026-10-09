
import pandas as pd
import numpy as np

INPUT_FILE = "financial_ratios.csv"
OUTPUT_FILE = "risk_assessment.csv"

df = pd.read_csv(INPUT_FILE)
df["Period"] = pd.to_datetime(df["Period"], errors="coerce")
df = df.sort_values(["Company", "Period"])

results = []

for company, group in df.groupby("Company"):
    group = group.sort_values("Period").reset_index(drop=True)
    latest = group.iloc[-1]
    previous = group.iloc[-2] if len(group) >= 2 else None

    business_signals = []
    data_warnings = []
    evidence = []

    growth = latest.get("Revenue Growth %", np.nan)
    margin = latest.get("Net Profit Margin %", np.nan)
    debt_equity = latest.get("Debt to Equity", np.nan)

    prior_margin = (
        previous.get("Net Profit Margin %", np.nan)
        if previous is not None else np.nan
    )

    margin_change = (
        margin - prior_margin
        if pd.notna(margin) and pd.notna(prior_margin)
        else np.nan
    )

    # Business signals: indicators to investigate, not predictions.
    if pd.notna(growth) and growth < 0:
        business_signals.append("Revenue contraction")
        evidence.append(f"Revenue growth: {growth:.2f}%.")

    if pd.notna(margin_change) and margin_change <= -2:
        business_signals.append("Net profit margin declined")
        evidence.append(
            f"Net profit margin changed by {margin_change:.2f} "
            "percentage points year over year."
        )

    # Data-quality warnings: large changes need contextual verification.
    if pd.notna(margin_change) and abs(margin_change) >= 5:
        data_warnings.append("Large year-over-year margin change")
        evidence.append(
            "Verify the reported figures, reporting basis, and exceptional "
            "items before interpreting the margin change."
        )

    if pd.notna(growth) and growth < -10:
        data_warnings.append("Large revenue decline")
        evidence.append(
            "Review the underlying statement and reporting comparability."
        )

    # Exclude banks from this preliminary debt/equity threshold.
    if latest.get("Sector Group") != "Banking" and pd.notna(debt_equity):
        if debt_equity > 2:
            business_signals.append("High debt/equity screening threshold")
            evidence.append(f"Debt/equity: {debt_equity:.2f}x.")

    if data_warnings:
        review_status = "Data verification required"
    elif business_signals:
        review_status = "Business review recommended"
    else:
        review_status = "No configured flags"

    results.append({
        "Company": company,
        "Period": latest["Period"].date(),
        "Review Status": review_status,
        "Business Signals": "; ".join(business_signals) or "None",
        "Data Quality Warnings": "; ".join(data_warnings) or "None",
        "Evidence": " ".join(evidence) or (
            "No configured rule was triggered. This does not mean "
            "the company is risk-free."
        ),
        "Revenue Growth %": growth,
        "Net Profit Margin %": margin,
        "Margin Change (pp)": margin_change,
        "Debt to Equity": debt_equity,
    })

assessment = pd.DataFrame(results)
assessment.to_csv(OUTPUT_FILE, index=False)

print("Evidence-aware screening complete.")
print("Companies assessed:", len(assessment))
print("Output:", OUTPUT_FILE)
print("\nResults:")
print(assessment[[
    "Company",
    "Review Status",
    "Business Signals",
    "Data Quality Warnings",
]].to_string(index=False))

print(
    "\nSource limitation: metrics come from Yahoo Finance and have not "
    "yet been independently reconciled against official filings."
)
