import yfinance as yf
import pandas as pd

# Define the ticker symbol
ticker_symbol = "MSFT"

# Get data for a single ticker
msft = yf.Ticker(ticker_symbol)

# Get historical market data (e.g., for the last month)
hist = msft.history(period="1mo")

# Print the data
print(hist.head())
