
from pathlib import Path

import pandas as pd

RATIOS_FILE = Path("financial_ratios.csv")
RISK_FILE = Path("risk_assessment.csv")

COMPANIES = []


def load_data():
    """Load and validate the financial datasets."""
    if not RATIOS_FILE.exists():
        raise FileNotFoundError(
            f"Missing {RATIOS_FILE}. Run financial_ratios.py first."
        )

    if not RISK_FILE.exists():
        raise FileNotFoundError(
            f"Missing {RISK_FILE}. Run risk_engine.py first."
        )

    ratios_df = pd.read_csv(RATIOS_FILE)
    risk_df = pd.read_csv(RISK_FILE)

    required_ratios = {
        "Company",
        "Period",
        "Revenue Growth %",
        "Net Profit Margin %",
        "Return on Assets %",
        "Debt to Equity",
    }

    required_risk = {
        "Company",
        "Period",
        "Review Status",
        "Business Signals",
        "Data Quality Warnings",
        "Evidence",
    }

    missing_ratios = required_ratios - set(ratios_df.columns)
    missing_risk = required_risk - set(risk_df.columns)

    if missing_ratios:
        raise ValueError(
            f"Missing columns in {RATIOS_FILE}: {sorted(missing_ratios)}"
        )

    if missing_risk:
        raise ValueError(
            f"Missing columns in {RISK_FILE}: {sorted(missing_risk)}"
        )

    ratios_df["Period"] = pd.to_datetime(
        ratios_df["Period"], errors="coerce"
    )
    risk_df["Period"] = pd.to_datetime(
        risk_df["Period"], errors="coerce"
    )

    return ratios_df, risk_df


ratios, risk = load_data()
COMPANIES = sorted(ratios["Company"].dropna().unique().tolist())


def clean_text(value, fallback="None"):
    """Convert missing or empty values into readable text."""
    if pd.isna(value):
        return fallback

    text = str(value).strip()

    if not text or text.casefold() in {"nan", "none", "null"}:
        return fallback

    return text


def fmt(value, suffix=""):
    """Format numeric values without displaying NaN."""
    if pd.isna(value):
        return "Unavailable"

    try:
        return f"{float(value):,.2f}{suffix}"
    except (TypeError, ValueError):
        return "Unavailable"


def latest_row(company):
    """Return the latest available ratio record for a company."""
    rows = ratios[
        ratios["Company"].astype(str).str.casefold()
        == company.casefold()
    ]

    rows = rows.dropna(subset=["Period"])

    if rows.empty:
        return None

    return rows.sort_values("Period").iloc[-1]


def find_company(question):
    """Match a company name mentioned in the question."""
    question_lower = question.casefold()

    matches = [
        company
        for company in COMPANIES
        if company.casefold() in question_lower
    ]

    return max(matches, key=len) if matches else None


def get_latest_risk_row(company):
    """Return the latest available risk assessment."""
    rows = risk[
        risk["Company"].astype(str).str.casefold()
        == company.casefold()
    ].dropna(subset=["Period"])

    if rows.empty:
        return None

    return rows.sort_values("Period").iloc[-1]


def explain_company(company):
    """Explain available company metrics and screening evidence."""
    row = latest_row(company)

    if row is None:
        return f"No financial data found for {company}."

    answer = [
        f"Company: {company}",
        f"Reporting period: {row['Period'].date()}",
        f"Revenue growth: {fmt(row.get('Revenue Growth %'), '%')}",
        f"Net profit margin: {fmt(row.get('Net Profit Margin %'), '%')}",
        f"Return on assets: {fmt(row.get('Return on Assets %'), '%')}",
        f"Debt/equity: {fmt(row.get('Debt to Equity'), 'x')}",
    ]

    risk_row = get_latest_risk_row(company)

    if risk_row is not None:
        answer.extend([
            f"Review status: {clean_text(risk_row.get('Review Status'), 'Unavailable')}",
            f"Business signals: {clean_text(risk_row.get('Business Signals'))}",
            f"Data warnings: {clean_text(risk_row.get('Data Quality Warnings'))}",
            f"Evidence: {clean_text(risk_row.get('Evidence'), 'No evidence available')}",
        ])
    else:
        answer.append("Risk assessment: Unavailable")

    answer.append(
        "Source limitation: Data is sourced from Yahoo Finance and has "
        "not been independently reconciled against official company filings."
    )

    answer.append(
        "Interpretation note: Screening indicators are preliminary and "
        "are not predictions or investment advice."
    )

    return "\n".join(answer)


def list_revenue_contractions():
    """List companies with negative latest available revenue growth."""
    latest = (
        ratios.dropna(subset=["Period"])
        .sort_values("Period")
        .groupby("Company")
        .tail(1)
    )

    flagged = latest[
        pd.to_numeric(latest["Revenue Growth %"], errors="coerce") < 0
    ].copy()

    if flagged.empty:
        return (
            "No revenue contractions were identified in the latest "
            "available records."
        )

    flagged = flagged.sort_values("Revenue Growth %")

    lines = [
        "Companies with negative latest reported revenue growth:",
        "",
    ]

    for _, row in flagged.iterrows():
        lines.append(
            f"- {row['Company']} ({row['Period'].date()}): "
            f"{fmt(row['Revenue Growth %'], '%')}"
        )

    lines.append(
        "\nThese are screening observations based on the available data."
    )

    return "\n".join(lines)


def answer_question(question):
    """Answer supported questions using the local financial datasets."""
    question = question.strip()

    if not question:
        return "Please enter a financial question."

    question_lower = question.casefold()

    # Handle cross-company questions before company-specific questions.
    if any(
        phrase in question_lower
        for phrase in [
            "revenue contraction",
            "revenue contractions",
            "companies have negative revenue",
            "which companies have negative revenue",
        ]
    ):
        return list_revenue_contractions()

    company = find_company(question)

    if company:
        return explain_company(company)

    return (
        "I couldn't identify a supported question from the current dataset.\n"
        "Try one of these:\n"
        "- Why was ITC flagged?\n"
        "- Explain Reliance Industries\n"
        "- What is TCS's revenue growth?\n"
        "- Which companies have revenue contraction?"
    )


if __name__ == "__main__":
    print("FinSight AI — Financial Q&A")
    print(f"Loaded financial data for {len(COMPANIES)} companies.")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            question = input("Ask a financial question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nFinSight AI closed.")
            break

        if question.casefold() in {"exit", "quit"}:
            print("Goodbye.")
            break

        print("\n" + answer_question(question) + "\n")
