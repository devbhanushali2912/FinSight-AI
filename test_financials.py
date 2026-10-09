
import yfinance as yf

ticker = "RELIANCE.NS"
stock = yf.Ticker(ticker)

print(f"Testing annual financial statements for {ticker}")

statements = {
    "Income Statement": stock.income_stmt,
    "Balance Sheet": stock.balance_sheet,
    "Cash Flow": stock.cashflow,
}

for name, statement in statements.items():
    print(f"\n--- {name} ---")

    if statement is None or statement.empty:
        print("No data returned.")
    else:
        print(statement.iloc[:, :4].to_string())
        print(f"\nRows available: {len(statement)}")
        print(f"Reporting periods available: {statement.shape[1]}")
