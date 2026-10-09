
import yfinance as yf

ticker = "RELIANCE.NS"

print(f"Testing market data for {ticker}...")

stock = yf.Ticker(ticker)
history = stock.history(period="1mo", interval="1d")

if history.empty:
    print("FAILED: No market data returned.")
else:
    print("SUCCESS: Market data received.")
    print(f"Rows retrieved: {len(history)}")
    print("\nLatest available prices:")
    print(history[["Open", "High", "Low", "Close", "Volume"]].tail())
