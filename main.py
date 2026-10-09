
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from financial_qa import COMPANIES, answer_question, explain_company

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="FinSight AI API",
    description="Financial analytics and evidence-based risk screening",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


def load_csv(filename):
    path = BASE_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def records_json(df):
    """Convert DataFrame records to JSON-safe dictionaries."""
    if df.empty:
        return []

    safe = df.astype(object).where(pd.notna(df), None)
    return safe.to_dict(orient="records")


def load_dashboard_data():
    ratios = load_csv("financial_ratios.csv")
    risk = load_csv("risk_assessment.csv")
    prices = load_csv("market_prices.csv")

    if not ratios.empty:
        ratios["Period"] = pd.to_datetime(
            ratios["Period"], errors="coerce"
        )

    if not risk.empty:
        risk["Period"] = pd.to_datetime(
            risk["Period"], errors="coerce"
        )

    if not prices.empty:
        prices["Date"] = pd.to_datetime(
            prices["Date"], errors="coerce"
        )

    return ratios, risk, prices


@app.get("/")
def home():
    return {
        "name": "FinSight AI",
        "status": "running",
        "companies_loaded": len(COMPANIES),
        "docs": "/docs",
    }


@app.get("/api/companies")
def list_companies():
    return {"companies": COMPANIES, "count": len(COMPANIES)}


@app.get("/api/dashboard")
def dashboard():
    ratios, risk, prices = load_dashboard_data()

    if ratios.empty:
        raise HTTPException(
            status_code=503,
            detail="Financial ratios are unavailable. Run financial_ratios.py.",
        )

    latest = (
        ratios.dropna(subset=["Period"])
        .sort_values("Period")
        .groupby("Company")
        .tail(1)
        .sort_values("Company")
    )

    merged = latest.merge(
        risk.dropna(subset=["Period"]),
        on=["Company", "Period"],
        how="left",
        suffixes=("", "_risk"),
    ) if not risk.empty else latest.copy()

    # Market prices are optional for the dashboard.
    market_summary = []
    if not prices.empty and {"Company", "Date", "Close"}.issubset(prices.columns):
        prices["Close"] = pd.to_numeric(prices["Close"], errors="coerce")
        prices = prices.dropna(subset=["Date", "Close"])

        for company, group in prices.groupby("Company"):
            group = group.sort_values("Date")
            if group.empty:
                continue

            first = group.iloc[0]
            last = group.iloc[-1]
            change = (
                (last["Close"] / first["Close"] - 1) * 100
                if first["Close"] != 0 else None
            )

            market_summary.append({
                "company": company,
                "ticker": last.get("Ticker"),
                "latest_close": float(last["Close"]),
                "period_change_pct": (
                    float(change) if pd.notna(change) else None
                ),
                "latest_date": last["Date"].strftime("%Y-%m-%d"),
            })

    review_col = "Review Status"
    warning_col = "Data Quality Warnings"
    signal_col = "Business Signals"

    if review_col in merged.columns:
        verification_count = int(
            merged[review_col].eq("Data verification required").sum()
        )
    else:
        verification_count = 0

    if signal_col in merged.columns:
        signal_count = int(
            merged[signal_col].fillna("None").ne("None").sum()
        )
    else:
        signal_count = 0

    return {
        "company_count": int(latest["Company"].nunique()),
        "latest_reporting_period": (
            latest["Period"].max().strftime("%Y-%m-%d")
            if latest["Period"].notna().any() else None
        ),
        "verification_required_count": verification_count,
        "companies_with_signals": signal_count,
        "companies": records_json(merged),
        "market_summary": market_summary,
        "source_note": (
            "Financial statements and ratios are sourced from Yahoo Finance "
            "and have not been independently reconciled against official filings. "
            "Market history is historical data, not a forecast."
        ),
    }


@app.get("/api/company/{company_name}")
def company_details(company_name: str):
    match = next(
        (
            company for company in COMPANIES
            if company.casefold() == company_name.casefold()
        ),
        None,
    )

    if match is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found in the current dataset.",
        )

    return {
        "company": match,
        "answer": explain_company(match),
    }


@app.get("/api/company/{company_name}/history")
def company_history(
    company_name: str,
    metric: str = Query(default="Net Profit Margin %"),
):
    allowed_metrics = {
        "Revenue",
        "Net Income",
        "Net Profit Margin %",
        "Return on Assets %",
        "Debt to Equity",
        "Revenue Growth %",
        "Operating Cash Flow",
        "Total Assets",
    }

    if metric not in allowed_metrics:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported metric.",
                "allowed_metrics": sorted(allowed_metrics),
            },
        )

    ratios, _, prices = load_dashboard_data()

    match = next(
        (
            company for company in COMPANIES
            if company.casefold() == company_name.casefold()
        ),
        None,
    )

    if match is None:
        raise HTTPException(status_code=404, detail="Company not found.")

    if ratios.empty or metric not in ratios.columns:
        raise HTTPException(status_code=503, detail="Metric data unavailable.")

    rows = ratios[
        ratios["Company"].astype(str).str.casefold() == match.casefold()
    ].dropna(subset=["Period"]).sort_values("Period")

    history = []
    for _, row in rows.iterrows():
        value = row.get(metric)
        history.append({
            "period": row["Period"].strftime("%Y-%m-%d"),
            "value": float(value) if pd.notna(value) else None,
        })

    price_history = []
    if not prices.empty and {"Company", "Date", "Close"}.issubset(prices.columns):
        selected = prices[
            prices["Company"].astype(str).str.casefold() == match.casefold()
        ].copy()

        selected["Close"] = pd.to_numeric(
            selected["Close"], errors="coerce"
        )
        selected = selected.dropna(subset=["Date", "Close"]).sort_values("Date")

        price_history = [
            {
                "date": row["Date"].strftime("%Y-%m-%d"),
                "close": float(row["Close"]),
            }
            for _, row in selected.iterrows()
        ]

    return {
        "company": match,
        "metric": metric,
        "history": history,
        "market_prices": price_history,
    }


@app.post("/api/ask")
def ask_question(request: QuestionRequest):
    answer = answer_question(request.question)

    return {
        "question": request.question,
        "answer": answer,
        "supported": not answer.startswith("I couldn't identify"),
    }
